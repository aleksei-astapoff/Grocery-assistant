from django.contrib import admin

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscribe, Tag)

RECIPE_LIMIT_SHOW = 5
admin.site.empty_value_display = '-Не задано-'

class RecipeIngredientAdmin(admin.StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_author', 'name', 'text',
        'cooking_time', 'get_tags', 'get_ingredients',
        'pub_date', 'get_favorite_count')
    search_fields = (
        'name', 'cooking_time',
        'author__email', 'ingredients__name')
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
        return '\n '.join([
            f'{item["ingredient__name"]} - {item["amount"]}'
            f' {item["ingredient__measurement_unit"]}.'
            for item in obj.recipe.values(
                'ingredient__name',
                'amount', 'ingredient__measurement_unit')])

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorite_recipe.count()
    


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'measurement_unit',)
    search_fields = (
        'name', 'measurement_unit',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'author', 'created',)
    search_fields = (
        'user__email', 'author__email',)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_recipe', 'get_count')

    @admin.display(
        description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} '
            for item in obj.recipe.values('name')[:RECIPE_LIMIT_SHOW]
        ]

    @admin.display(
        description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()


@admin.register(ShoppingCart)
class SoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_recipe', 'get_count')

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} '
            for item in obj.recipe.values('name')[:RECIPE_LIMIT_SHOW]
        ]

    @admin.display(description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()
