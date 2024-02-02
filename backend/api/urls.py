from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientsViewSet, RecipesViewSet,
                       TagsViewSet, UsersViewSet,)

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('users', UsersViewSet)
router_v1.register('tags', TagsViewSet)
router_v1.register('ingredients', IngredientsViewSet)
router_v1.register('recipes', RecipesViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
