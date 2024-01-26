# Generated by Django 4.2.9 on 2024-01-24 07:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_recipeingredient_amount_alter_tag_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipeingredient',
            options={'ordering': ['-id'], 'verbose_name': 'Ингредиент', 'verbose_name_plural': 'Количество ингредиентов'},
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient', to='recipes.ingredient', verbose_name='Ингредиент'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe', to='recipes.recipe', verbose_name='Рецепт'),
        ),
    ]