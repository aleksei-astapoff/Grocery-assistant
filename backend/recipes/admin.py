import webcolors
from django.contrib import admin
from django.utils.safestring import mark_safe

from foodgram.constant import (MIN_VALUE_IGRREDIENTS_ADMIN,
                               NO_VALUE)
from .models import (FavoriteRecipe, Ingredient, Recipe,
                     RecipeIngredient, ShoppingCart, Tag)


admin.site.empty_value_display = NO_VALUE


class RecipeIngredientAdmin(admin.StackedInline):
    """Административная панель связи  Рецептов и Ингредиентов."""

    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)
    min_num = MIN_VALUE_IGRREDIENTS_ADMIN


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административная панель Рецептов."""

    list_display = (
        'id', 'get_image', 'get_author', 'name', 'text',
        'cooking_time', 'get_tags', 'get_ingredients',
        'pub_date', 'get_favorite_count',
    )
    search_fields = (
        'name', 'cooking_time',
        'author__email', 'ingredients__name',
    )
    list_filter = ('pub_date', 'tags',)

    inlines = (RecipeIngredientAdmin,)

    @admin.display(description='Электронная почта автора',)
    def get_author(self, obj):
        return obj.author.email

    @admin.display(description='Тэги')
    def get_tags(self, obj):
        tags_names = [_.name for _ in obj.tags.all()]
        return ', '.join(tags_names)

    @admin.display(description=' Ингредиенты ')
    def get_ingredients(self, obj):
        return ', '.join([
            f'{item["ingredient__name"]} - {item["amount"]}'
            f' {item["ingredient__measurement_unit"]}.'
            for item in obj.recipe.values(
                'ingredient__name',
                'amount', 'ingredient__measurement_unit')])

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorite_recipe.count()

    @admin.display(description='Изображение')
    def get_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60">'
            )
        return f'{NO_VALUE}'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административная панель Тэгов."""

    list_display = (
        'id', 'name', 'color_name',
        'color', 'slug',
    )
    search_fields = ('name', 'slug',)

    def color_name(self, obj):
        try:
            return webcolors.hex_to_name(obj.color)
        except ValueError:
            return obj.color
    color_name.short_description = 'Название цвета'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административная панель Ингредиентов."""

    list_display = (
        'id', 'name', 'measurement_unit',
    )
    search_fields = (
        'name', 'measurement_unit',
    )
    list_editable = (
        'name', 'measurement_unit'
    )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """Административная панель Избранных Рецептов Пользователя."""

    list_display = ('pk', 'user', 'recipe')


@admin.register(ShoppingCart)
class SoppingCartAdmin(admin.ModelAdmin):
    """Административная панель Корзины Пользователя. """

    list_display = ('id', 'user', 'recipe')
