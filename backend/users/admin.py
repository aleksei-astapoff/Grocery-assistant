from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Subscribe
from .forms import UserForm


User = get_user_model()

admin.site.empty_value_display = '-Не задано-'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """"Административная панель Пользователя"""
    form = UserForm

    list_display = (
        'id', 'is_blocked', 'username', 'email',
        'first_name', 'last_name', 'date_joined',)
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'first_name', 'is_blocked')
    readonly_fields = ('last_login',)
    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Permissions', {'fields': ('is_staff', 'is_blocked')}),

    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Permissions', {'fields': ('is_staff', 'is_blocked')}),
    )


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Административная панель Подписок Пользователя """

    list_display = (
        'id', 'user', 'author', 'created',)
    search_fields = (
        'user__email', 'author__email',)
