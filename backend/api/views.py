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
                          RecipeWriteSerializer, SubscriptionsSerializer,
                          TagSerializer, ObjectRecipeSerializer,
                          SubscribeSerializer, CustomUserSerializer,)
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
        ).order_by('following__user')
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        data = {'user': request.user.id, 'author': author.id}
        serializer = SubscribeSerializer(data=data,
                                         context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        subscription = Subscribe.objects.filter(
            user=request.user, author_id=id
        )
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"errors": "Подписка не найдена."},
                        status=status.HTTP_404_NOT_FOUND)


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с Рецептами."""

    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

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
            ).order_by('-pub_date')
            
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def create_shopping_list(ingredients):
        content = 'Список покупок:\n\n'
        for num, index in enumerate(ingredients):
            content += (
                f'{num + 1}. {index["ingredient__name"]} - '
                f'{index["amount"]} {index["ingredient__measurement_unit"]}\n'
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
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        return self.create_shopping_list(ingredients)
    
    def add_delete_recipe(self, pk, model):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        storage, created_storage  = model.objects.get_or_create(user=user)

        if self.request.method == 'POST':
            if storage.recipe.filter(pk=recipe.pk).exists():
                raise ValidationError(
                    'Рецепт уже находится в вашем списке.'
                )
            storage.recipe.add(recipe)
            serializer = ObjectRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if storage.recipe.filter(pk=recipe.pk).exists():
                storage.recipe.remove(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=True)
    def favorite(self, request, pk):
        return self.add_delete_recipe(pk, FavoriteRecipe)

    @action(methods=['POST', 'DELETE'], detail=True)
    def shopping_cart(self, request, pk):
        return self.add_delete_recipe(pk, ShoppingCart)


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
