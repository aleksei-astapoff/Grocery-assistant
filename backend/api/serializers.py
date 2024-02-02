from django.core.validators import MinValueValidator, MaxValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User
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


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для обработки запросов, Сохранения Пользователей."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }


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
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=MIN_VALUE_AMOUNT,
        max_value=MAX_VALUE_AMOUNT,
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
        validators=[
            MinValueValidator(
                MIN_VALUE_TIME,
                message=f'Мин. время приготовления {MIN_VALUE_TIME} минута'
            ),
            MaxValueValidator(
                MAX_VALUE_TIME,
                message=f'Макс. время приготовления {MAX_VALUE_TIME} минут'
            ),
        ],
    )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        print(data.get('ingredients'))
        ingredient_ids = [item['ingredient'] for item in data['ingredients']]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальными!'}
            )
        if not data['tags']:
            raise serializers.ValidationError(
                'Нужен хотя бы один тэг для рецепта!'
            )

        tag_ids = [item.id for item in data['tags']]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальными!'}
            )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        ingredients_to_create = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient.get('ingredient'),
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


class SubscribeSerializer(CustomUserSerializer):
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
            limit = 0

        if limit > 0:
            recipes = obj.recipe.all()[:limit]
        else:
            recipes = obj.recipe.all()

        return ObjectRecipeSerializer(
            recipes,
            many=True,
            context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipe.count()
