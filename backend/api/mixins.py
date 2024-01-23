from django.shortcuts import get_object_or_404

from rest_framework.permissions import AllowAny

from recipes.models import Recipe
from .permissions import IsAdminOrReadOnly
from .serializers import SubscribeRecipeSerializer


class ObjectMixin:

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (AllowAny,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe


class PermissionMixin:

    permission_classes = (IsAdminOrReadOnly,)
