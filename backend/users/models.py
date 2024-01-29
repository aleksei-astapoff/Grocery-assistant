import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_LENGTH_EMAIL_FIELD = 254
MAX_LENGTH_CHAR_FIELD = 150


class User(AbstractUser):
    """Модель Пользователя."""

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
    is_blocked = models.BooleanField(
        default=False,
        verbose_name='Заблокирован',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.username or self.username.isspace():
            self.username = self.email
        super().save(*args, **kwargs)

    def create_superuser(self, email, password):
        user = self.create_user(email=email)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        return super().save()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-date_joined',)

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
    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created']
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
