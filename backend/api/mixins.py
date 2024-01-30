from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated

from recipes.models import Recipe
from .permissions import IsAdminOrReadOnly
from .serializers import SubscribeRecipeSerializer


class ObjectMixin:
    """Миксин для работы с Избранным и Корзиной."""

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe


class PermissionMixin:
    """Миксин для работы с Тэгами и Ингредиентами."""

    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None
    http_method_names = ('get',)
