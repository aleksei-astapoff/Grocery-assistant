from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.db.models import BooleanField
from django.http import FileResponse
from django.shortcuts import get_object_or_404


from djoser.views import UserViewSet

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, Recipe, 
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscribe
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrAdmin
from .mixins import ObjectMixin, PermissionMixin
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SubscribeSerializer,
                          TagSerializer, UserCreateSerializer,
                          UserListSerializer, UserPasswordSerializer)

User = get_user_model()


class UsersViewSet(UserViewSet):

    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.annotate(
                is_subscribed=Exists(
                    self.request.user.follower.filter(
                        author=OuterRef('id'))
                )).prefetch_related(
                    'follower', 'following'
            )
        else:
            return User.objects.annotate(
                is_subscribed=BooleanField(default=False))

    def get_serializer_class(self):
        if self.request.method.lower() == 'post':
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(
            user=user).select_related('author').annotate(
            recipes_count=Count('author__recipe'),
            is_subscribed=Value(True, output_field=BooleanField())
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class AddAndDeleteSubscribe(generics.RetrieveDestroyAPIView,
                            generics.ListCreateAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True), )

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя!'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=instance).exists():
            return Response(
                {'errors': 'Уже есть подписка!'},
                status=status.HTTP_400_BAD_REQUEST)
        subs = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subs)
        serialized_data = serializer.data
        serialized_data['recipes_count'] = instance.recipe.count()
        serialized_data['is_subscribed'] = True
        return Response(serialized_data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        subscription = get_object_or_404(Subscribe, author=instance)
        if subscription.user != self.request.user:
            raise ValidationError('Ошибка отписки.')
        subscription.delete()


class RecipesViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_base_queryset(self):
        return Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        )

    def get_annotated_queryset(self, user):
        if user.is_authenticated:
            return self.get_base_queryset().annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(
                        user=user,
                        recipe=OuterRef('id'),
                    )),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('id'),
                    ))
            )
        else:
            return self.get_base_queryset().annotate(
                is_in_shopping_cart=BooleanField(default=False),
                is_favorited=BooleanField(default=False),
            )

    def get_queryset(self):
        return self.get_annotated_queryset(self.request.user)

    def perform_create(self, serializer):
        recipe = serializer.save(author=self.request.user)
        user = self.request.user
        if user.is_authenticated:
            recipe.is_favorited = FavoriteRecipe.objects.filter(
                user=user, recipe=recipe
            ).exists()
            recipe.is_in_shopping_cart = ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists()
        else:
            recipe.is_favorited = BooleanField(default=False)
            recipe.is_in_shopping_cart = BooleanField(default=False)
        return recipe
    
    def is_author_or_admin(self):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
        if not (
            recipe.author == self.request.user or self.request.user.is_staff
        ):
            raise PermissionDenied(
                'У вас недостаточно прав для выполнения данного действия.'
            )
        return recipe

    def update(self, request, *args, **kwargs):
        self.is_author_or_admin()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self.is_author_or_admin()
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        self.is_author_or_admin()

        return super().destroy(request, *args, **kwargs)


@api_view(['post'])
def set_password(request):
    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль изменен!'},
            status=status.HTTP_201_CREATED)
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


class AddDeleteFavoriteRecipe(
        ObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        favorite_recipe = request.user.favorite_recipe
        if instance in favorite_recipe.recipe.all():
            raise ValidationError(
                'Рецепт уже находится в избранном.'
            )
        favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        favorite_recipe = self.request.user.favorite_recipe
        if instance in favorite_recipe.recipe.all():
            favorite_recipe.recipe.remove(instance)
        else:
            raise ValidationError(
                'Рецепт отсутствует в вашем списке избранного.'
            )


class AddDeleteShoppingCart(
        ObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        shopping_cart = request.user.shopping_cart
        if instance in shopping_cart.recipe.all():
            raise ValidationError(
                'Рецепт уже находится в вашем списке покупок.'
            )
        shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        shopping_cart = self.request.user.shopping_cart
        if instance in shopping_cart.recipe.all():
            shopping_cart.recipe.remove(instance)
        else:
            raise ValidationError(
                'Рецепт отсутствует в вашем списке покупок.'
            )


class TagsViewSet(
        PermissionMixin,
        viewsets.ModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(
        PermissionMixin,
        viewsets.ModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


@api_view(['GET'],)
def download_shopping_cart(request):
    pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont('Vera', 20)
    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(amount=Sum('amount'))

    p.drawString(100, 800, "Cписок покупок:")

    height = 775
    for num, i in enumerate(ingredients):
        ingredient_string = (
            f'{num + 1}. {i["ingredient__name"]} - '
            f'{i["amount"]} {i["ingredient__measurement_unit"]}'
        )
        p.drawString(100, height, ingredient_string)
        height -= 25

    p.showPage()
    p.save()

    buffer.seek(0)
    response = FileResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.pdf"'
    )
    return response
