from django.db.models.aggregates import Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.db.models import BooleanField
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscribe, User
from .filters import IngredientFilter, RecipeFilter
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SubscribeSerializer,
                          TagSerializer, ObjectRecipeSerializer,
                          CustomUserSerializer,)
from .permissions import IsAuthorOrAdminOrReadOnly
from .pagination import LimitPagination


class UsersViewSet(UserViewSet):
    """Вьюсет для работы с Пользователями."""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializers_class = CustomUserSerializer
    pagination_class = LimitPagination
    lookup_field = 'id'

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),)
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(
            following__user=user).annotate(
            is_subscribed=Value(True, output_field=BooleanField())
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user
        subscription = Subscribe.objects.filter(user=user, author=author)
        if subscription.exists():
            return Response(
                {'errors': 'Уже есть подписка!'},
                status=status.HTTP_400_BAD_REQUEST)
        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя!'},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscribeSerializer(author, context={'request': request})
        Subscribe.objects.create(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        print("start")
        author = get_object_or_404(User, id=id)
        print(author)
        user = request.user
        print(user)
        subscription = Subscribe.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'errors': 'Подписка не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с Рецептами."""

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        )
        if user.is_authenticated:
            return queryset.annotate(
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
            return queryset.annotate(
                is_in_shopping_cart=Value(False, output_field=BooleanField()),
                is_favorited=Value(False, output_field=BooleanField()),
            )

    @staticmethod
    def create_shopping_list(ingredients):
        content = "Список покупок:\n\n"
        for num, i in enumerate(ingredients):
            content += (
                f'{num + 1}. {i["ingredient__name"]} - '
                f'{i["amount"]} {i["ingredient__measurement_unit"]}\n'
            )
        response = FileResponse(
            content, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated],)
    def download_shopping_cart(self, request):
        """Функция выполняющая выгрузку Корзины Пользователя в TXT формате."""

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        return self.create_shopping_list(ingredients)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        instance = get_object_or_404(Recipe, id=pk)
        shopping_cart, created_shopping_cart = (
            ShoppingCart.objects.get_or_create(user=request.user)
        )
        if instance in shopping_cart.recipe.all():
            raise ValidationError(
                'Рецепт уже находится в вашем списке покупок.'
            )
        shopping_cart.recipe.add(instance)
        serializer = ObjectRecipeSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingCart,
            user=request.user.id,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        favorite_recipe, created_favorite = (
            FavoriteRecipe.objects.get_or_create(user=request.user)
        )
        instance = get_object_or_404(Recipe, id=pk)
        if instance in favorite_recipe.recipe.all():
            raise ValidationError(
                'Рецепт уже находится в избранном.'
            )
        favorite_recipe.recipe.add(instance)
        serializer = ObjectRecipeSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            FavoriteRecipe,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с Тэгами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ('get',)


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с Ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None
    http_method_names = ('get',)
