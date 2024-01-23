from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Exists, OuterRef, Value

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet

from reportlab.pdfgen import canvas

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, Recipe, 
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscribe
from .filters import IngredientFilter, RecipeFilter
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
        return User.objects.annotate(
            is_subscribed=Exists(
                self.request.user.follower.filter(
                    author=OuterRef('id'))
            )).prefetch_related(
                'follower', 'following'
        ) if self.request.user.is_authenticated else User.objects.annotate(
            is_subscribed=Value(False))

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
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class AddAndDeleteSubscribe(
        generics.ListCreateAPIView,
        generics.RetrieveDestroyAPIView):

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            recipes_count=Count('following__recipe'),
            is_subscribed=Value(True),
        )

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            return Response(
                {'errors': 'Нельзя  подписаться на самого себя!'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=instance).exists():
            return Response(
                {'errors': 'Нельзя  подписаться дважды!'},
                status=status.HTTP_400_BAD_REQUEST)
        subscribe = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subscribe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.follower.filter(author=instance).delete()


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
                is_in_shopping_cart=Value(False),
                is_favorited=Value(False),
            )

    def get_queryset(self):
        return self.get_annotated_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@api_view(['post'])
def set_password(request):
    """Изменить пароль."""

    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль изменен!'},
            status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Введите верные данные!'},
        status=status.HTTP_400_BAD_REQUEST)


class AddDeleteFavoriteRecipe(
        ObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.favorite_recipe.recipe.remove(instance)


class AddDeleteShoppingCart(
        ObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.shopping_cart.recipe.remove(instance)


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


@api_view(['GET'])
def download_shopping_cart(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=request.user
    ).values(
        'ingredient__name', 'unique_ingredient'
    ).annotate(amount=Sum('amount'))

    p.drawString(100, 800, "Cписок покупок:")

    height = 800
    for num, i in enumerate(ingredients):
        ingredient_string = (
            f'{num}. {i["ingredient__name"]} - '
            f'{i["amount"]} {i["unique_ingredient"]}'
        )
        p.drawString(100, height, ingredient_string)
        height -= 25

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.pdf"'
    )
    return response
