from django import forms
from django.contrib.auth.forms import UserChangeForm

from .models import User


class UserForm(UserChangeForm):
    """"Форма для настройки поля Пароль в Админпанели."""

    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Оставьте это поле пустым, чтобы сохранить текущий пароль."
    )

    class Meta:
        model = User
        fields = '__all__'
