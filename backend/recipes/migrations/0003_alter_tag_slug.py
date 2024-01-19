# Generated by Django 4.2.9 on 2024-01-19 12:16

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=200, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_slug', message="Ссылка должна содержать только буквы, '                     'цифры, дефис или подчеркивание.", regex='^[-a-zA-Z0-9_]+$')], verbose_name='Ссылка'),
        ),
    ]
