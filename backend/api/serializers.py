import base64

import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscribe

User = get_user_model()


class SubscribedMixin:
    """Миксин для работы с Подписками"""

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.follower.filter(author=obj).exists()
            if user.is_authenticated
            else False
        )


class Base64ImageField(serializers.ImageField):
    """Сериализатор для Загрузки Изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='temp.{}'.format(ext)
            )

        return super().to_internal_value(data)


class UserListSerializer(SubscribedMixin, serializers.ModelSerializer):
    """Сериализатор для обработки запросов по Представлению Пользователей"""

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        read_only_fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки запросов, Сохранения Пользователей."""

    username = serializers.CharField(required=False,)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )

    def validate_email(self, value):
        try:
            django_validate_email(value)
        except ValidationError as exc:
            raise serializers.ValidationError(
                'Введите корректный адрес электронной почты.'
            ) from exc

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Этот email уже используется.')

        return value

    def validate_password(self, password):
        validators.validate_password(password)
        return password

    def to_internal_value(self, data):
        if 'username' not in data or not data['username']:
            data['username'] = data['email']
        return super().to_internal_value(data)


class UserPasswordSerializer(serializers.Serializer):
    """Сериализатор для обработки смены пароля пользователя."""

    new_password = serializers.CharField(
        label='Новый пароль',
    )
    current_password = serializers.CharField(
        label='Текущий пароль',
    )

    def validate_current_password(self, current_password):
        user = self.context['request'].user
        if not authenticate(
                username=user.email,
                password=current_password):
            raise serializers.ValidationError(
                'Доступ запрещен, проверьте введеные данные!',
                code='authorization')
        return current_password

    def validate_new_password(self, new_password):
        validators.validate_password(new_password)
        return new_password

    def create(self, validated_data):
        user = self.context['request'].user
        user.password = make_password(
            validated_data.get('new_password'))
        user.save()
        return validated_data


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


class RecipeUserSerializer(SubscribedMixin, serializers.ModelSerializer):
    """Сериализатор для обработки данных для связей Рецепты-Подписчики."""
    is_subscribed = serializers.SerializerMethodField(
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
        )


class IngredientsEditSerializer(serializers.ModelSerializer):
    """Сериализатор для выбора Ингредиентов."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

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
        use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = IngredientsEditSerializer(
        many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        ingredient_ids = [item.get('id') for item in data['ingredients']]
        ingredient_list = []
        for ingredient_id in ingredient_ids:
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError({'ingredients': [
                    f'Ингредиента с id {ingredient_id} нет в базе данных.'
                ]})
            if ingredient_id in ingredient_list:
                raise serializers.ValidationError({'ingredients': [
                    'Ингредиент должен быть уникальным!'
                ]})
            ingredient_list.append(ingredient_id)
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен хотя бы один тэг для рецепта!')
        for tag_name in tags:
            if not Tag.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f'Тэга {tag_name} не существует!')
        return data

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Убедитесь, что время приготовления больше либо равно 1')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Минимальное количество: 1 ингредиент в рецепте!')
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Убедитесь, количество ингредиента больше либо равно 1.')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'), )

    def create(self, validated_data):
        print("Validated data:", validated_data)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для выгрузки Рецептов."""

    image = serializers.ImageField(use_url=True)
    tags = TagSerializer(
        many=True,
        read_only=True)
    author = RecipeUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source='recipe')
    is_favorited = serializers.BooleanField(
        read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class ObjectRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для выгрузки Подписки Избранного Корзины."""
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки подписок."""
    id = serializers.IntegerField(
        source='author.id')
    email = serializers.EmailField(
        source='author.email')
    username = serializers.CharField(
        source='author.username')
    first_name = serializers.CharField(
        source='author.first_name')
    last_name = serializers.CharField(
        source='author.last_name')
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(
        read_only=True)
    recipes_count = serializers.IntegerField(
        read_only=True)

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.author.recipe.all()[:int(limit)] if limit
            else obj.author.recipe.all())
        return ObjectRecipeSerializer(
            recipes,
            many=True).data
