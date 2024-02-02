import django_filters as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Поиск по полю в Ингредиентах."""
    name = filters.CharFilter(
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Поиск и фильтрация в Рецептах."""

    is_in_shopping_cart = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(),
        label='В корзине.',
    )
    is_favorited = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(),
        label='В избранных.',
    )
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Ссылка',
    )

    class Meta:
        model = Recipe
        fields = (
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'tags',
        )
