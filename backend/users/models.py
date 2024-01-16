from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_LENGTH_EMAIL_FIELD = 254
MAX_LENGTH_CHAR_FIELD = 150


class User(AbstractUser):
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
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-date_joined',)

    def __str__(self):
        return self.email
