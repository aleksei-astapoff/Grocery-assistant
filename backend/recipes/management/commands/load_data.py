
import csv

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Команда загрузки Ингредиентов в Базу Данных."""

    help = 'Загрузка из csv файлов'

    def handle(self, *args, **kwargs):
        ingredient_file_path = f'{settings.BASE_DIR}/data/ingredients.csv'
        tag_file_path = f'{settings.BASE_DIR}/data/tags.csv'
        try:
            with open(
                ingredient_file_path, 'r', encoding='utf-8'
            ) as ingredient_file:
                reader = csv.reader(ingredient_file)
                for row in reader:
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name, measurement_unit=measurement_unit
                    )

            with open(tag_file_path, 'r', encoding='utf-8') as tag_file:
                reader = csv.reader(tag_file)
                for row in reader:
                    name, color, slug = row
                    Tag.objects.get_or_create(
                        name=name, color=color, slug=slug
                    )

            self.stdout.write(self.style.SUCCESS(
                'Ингредиенты и теги загружены!'
            ))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Один из файлов не найден. провеьте, что оба файла существуют.'
            ))
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f'Произошла ошибка: {str(exc)}')
            )
