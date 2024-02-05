from django.db.models.aggregates import Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.db.models import BooleanField
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
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
                          TagSerializer, FavoriteSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        subscription = Subscribe.objects.filter(
            user=request.user, author_id=id
        )
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Подписка не найдена.'},
                        status=status.HTTP_404_NOT_FOUND)


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с Рецептами."""

    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related('author')
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
        """Метод выполняющий выгрузку Корзины Пользователя в TXT формате."""

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        return self.create_shopping_list(ingredients)

    @staticmethod
    def add_recipe(request, pk, serializers):
        context = {'request': request}
        # recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializers(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_recipe(request, pk, serializers):
        recipe = serializers.Meta.model.objects.filter(
            user=request.user,
            recipe_id=pk
        )
        if recipe.exists():
            recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self.add_recipe(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        return self.delete_recipe(request, pk, ShoppingCartSerializer)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        return self.add_recipe(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        return self.delete_recipe(request, pk, FavoriteSerializer)


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
