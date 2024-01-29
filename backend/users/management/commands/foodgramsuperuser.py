import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from dotenv import load_dotenv

load_dotenv()

User = get_user_model()


class Command(BaseCommand):
    """Команда для создания Суперпользователя."""
    help = 'Создание суперпользователя'

    def handle(self, *args, **kwargs):

        username = os.getenv('SUPERUSER_USERNAME')
        email = os.getenv('SUPERUSER_EMAIL')
        password = os.getenv('SUPERUSER_PASSWORD')

        if (User.objects.filter(username=username).exists()
                or User.objects.filter(email=email).exists()):
            self.stderr.write(self.style.ERROR(
                'Суперпользователь уже существует'
            ))
            return

        try:
            user = User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(
                f'Суперпользователь успешно создан: {user.username}'
            ))
        except IntegrityError:
            self.stderr.write(self.style.ERROR(
                 'Возникла ошибка при создании Суперпользователя'
            ))
