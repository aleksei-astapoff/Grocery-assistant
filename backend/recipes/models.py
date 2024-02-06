from django.core import validators
from django.db import models
from colorfield.fields import ColorField

from users.models import User
from foodgram.constant import (MAX_LENGTH_CHAR_FIELD, COLOR_PALETTE,
                               MIN_VALUE_TIME, MAX_VALUE_TIME,
                               MIN_VALUE_AMOUNT, MAX_VALUE_AMOUNT,)


class Ingredient(models.Model):
    """Модель Ингредиентов."""

    name = models.CharField(
        'Название ингредиента',
        max_length=MAX_LENGTH_CHAR_FIELD,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH_CHAR_FIELD,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_measurement'
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tag(models.Model):
    """Модель Тэгов."""

    name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_CHAR_FIELD,
    )
    color = ColorField(
        'Цвет',
        format='hex',
        samples=COLOR_PALETTE,
    )
    slug = models.SlugField(
        'Ссылка',
        max_length=MAX_LENGTH_CHAR_FIELD,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель Рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        'Название рецепта',
        max_length=MAX_LENGTH_CHAR_FIELD,
    )
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='static/recipe/',
        blank=True,
        null=True,
    )
    text = models.TextField(
        'Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(
            validators.MaxValueValidator(
                MAX_VALUE_TIME,
                message=f'Макс. время приготовления {MAX_VALUE_TIME} минут'
            ),
            validators.MinValueValidator(
                MIN_VALUE_TIME,
                message=f'Мин. время приготовления {MIN_VALUE_TIME} минута'
            ),
        ),
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author.email}, {self.name}'


class RecipeIngredient(models.Model):
    """Модель связи моделей Рецептов и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        default=MIN_VALUE_AMOUNT,
        validators=(
            validators.MaxValueValidator(
                MAX_VALUE_AMOUNT,
                message=f'Макс. количество ингридиентовя {MAX_VALUE_AMOUNT} '
            ),
            validators.MinValueValidator(
                MIN_VALUE_AMOUNT,
                message=f'Мин. количество ингридиентов {MIN_VALUE_AMOUNT}'
            ),
        ),
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ('recipe', 'amount',)
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient'
            ),
        )


class UserRecipeRelation(models.Model):
    """Абстрактная модель для Избранного и Корзины"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ('user',)

    def __str__(self):
        return (f'Пользователь {self.user} добавил'
                f'{self.user} добавил рецепт {self.recipe.name}'
                f' в {self._meta.verbose_name}')


class FavoriteRecipe(UserRecipeRelation):
    """Модель избранных рецептов пользователя."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorite_recipe'

    def __str__(self):
        return super().__str__() + ' в избранное.'


class ShoppingCart(UserRecipeRelation):
    """"Модель корзины пользователя."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return super().__str__() + ' в покупки.'
