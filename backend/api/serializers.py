from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            Tag, FavoriteRecipe, ShoppingCart)
from users.models import Subscribe, User
from foodgram.constant import (MIN_VALUE_TIME, MAX_VALUE_TIME,
                               MAX_VALUE_AMOUNT, MIN_VALUE_AMOUNT)


class CustomUserSerializer(UserSerializer):
    """Сериализатор для обработки запросов по Представлению Пользователей"""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.follower.filter(author=obj).exists())


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки Тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки Ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки данных для связей Рецепты-Ингредиенты"""

    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsEditSerializer(serializers.ModelSerializer):
    """Сериализатор для выбора Ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=MIN_VALUE_AMOUNT,
        max_value=MAX_VALUE_AMOUNT,
        error_messages={
            'min_value': 'Количество должно быть не меньше {min_value}.',
            'max_value': 'Количество не должно превышать {max_value}.',
            'invalid': 'Пожалуйста, введите корректное число.',
        },
    )

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'amount',
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для Записи/Обновления Рецептов."""

    image = Base64ImageField(
        max_length=None,
        use_url=True,
        allow_null=False,
        allow_empty_file=False,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = IngredientsEditSerializer(
        many=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE_TIME,
        max_value=MAX_VALUE_TIME,
        error_messages={
            'min_value': 'Мин. время приготовления {min_value} минута.',
            'max_value': 'Макс. время приготовления{max_value} минут.',
            'invalid': 'Пожалуйста, введите корректное число.',
        },
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        print(data)
        if 'ingredients' not in data or not data['ingredients']:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент для рецепта!'}
            )

        ingredient_ids = [item['id'] for item in data['ingredients']]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальными!'}
            )
        if not data['tags']:
            raise serializers.ValidationError(
                'Нужен хотя бы один тэг для рецепта!'
            )

        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальными!'}
            )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        ingredients_to_create = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_to_create)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        user = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data, author=user)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        self.create_ingredients(validated_data.pop('ingredients'), instance)
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для выгрузки Рецептов."""

    image = serializers.ImageField(use_url=True)
    tags = TagSerializer(
        many=True,
        read_only=True)
    author = CustomUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source='recipe',
    )
    is_favorited = serializers.BooleanField(
        read_only=True,
        default=False,)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False,)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class ObjectRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор представления(отображения) Избранного и Корзины."""
    image = serializers.ImageField(use_url=True,
                                   read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления/удаления рецепта в избранное."""
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')

    def validate(self, data):
        user, recipe = data.get('user'), data.get('recipe')
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'Этот рецепт уже добавлен'}
            )
        return data

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ObjectRecipeSerializer(instance.recipe, context=context).data


class ShoppingCartSerializer(FavoriteSerializer):
    """Сериализатор добавления/удаления рецепта в список покупок."""
    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор для обработки подписок."""
    recipes = SerializerMethodField(read_only=True)
    recipes_count = SerializerMethodField(read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = (
            CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
        )

    def get_recipes(self, obj):
        request = self.context['request']
        try:
            limit = int(request.GET.get('recipes_limit', 0))
        except ValueError:
            limit = None
            recipes = obj.recipe.all()[:limit]

            return ObjectRecipeSerializer(
                recipes,
                many=True,
                context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipe.count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['user', 'author']

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Subscribe.objects.filter(
            user=data['user'], author=data['author']
        ).exists():
            raise serializers.ValidationError('Уже есть подписка.')
        return data

    def to_representation(self, instance):
        author = instance.author
        serializer = SubscriptionsSerializer(author, context=self.context)
        return serializer.data
