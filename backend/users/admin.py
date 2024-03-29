from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe, User
from .forms import UserForm


admin.site.empty_value_display = '-Не задано-'


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    """"Административная панель Пользователей"""

    form = UserForm

    list_display = (
        'id', 'username', 'email',
        'first_name', 'last_name', 'date_joined',
        'get_recipe_count', 'get_follower_count')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'first_name',)
    readonly_fields = ('last_login',)
    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Permissions', {'fields': ('is_staff',)}),

    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2',
                       'username', 'first_name', 'last_name',),
        }),
        ('Permissions', {'fields': ('is_staff',)}),
    )

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

    @admin.display(description='Количество рецептов')
    def get_recipe_count(self, obj):
        return obj.recipe.count()

    @admin.display(description='Количество подписчиков')
    def get_follower_count(self, obj):
        return obj.follower.count()


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Административная панель Подписок Пользователя """

    list_display = (
        'id', 'user', 'author',)
    search_fields = (
        'user__email', 'author__email',)
