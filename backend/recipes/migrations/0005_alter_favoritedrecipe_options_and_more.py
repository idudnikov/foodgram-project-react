# Generated by Django 4.0.6 on 2022-07-20 05:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_ingredient_options_alter_recipe_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favoritedrecipe',
            options={'verbose_name': 'Избранное', 'verbose_name_plural': 'Избранные'},
        ),
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={'verbose_name': 'Корзина', 'verbose_name_plural': 'Корзины'},
        ),
    ]
