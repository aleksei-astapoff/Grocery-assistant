import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.constant import (MAX_LENGTH_EMAIL_FIELD, MAX_LENGTH_CHAR_FIELD,
                               USERNAME,)


class User(AbstractUser):
    """Модель Пользователя."""

    USERNAME_FIELD = USERNAME
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        'Электронная почта',
        max_length=MAX_LENGTH_EMAIL_FIELD,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH_CHAR_FIELD,
        unique=True,
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_CHAR_FIELD,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_CHAR_FIELD,
    )
    password = models.CharField(
        'Пароль',
        max_length=MAX_LENGTH_CHAR_FIELD,
        validators=[validators.validate_password],
        help_text=('Пароль должен соответствовать требованиям безопасности.'),
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return (
            f'Username: {self.username}, '
            f'Email: {self.email}'
        )


class Subscribe(models.Model):
    """"Модель Подписок Пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user', )
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на автора {self.author}'

    def clean(self) -> None:
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя')

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)
