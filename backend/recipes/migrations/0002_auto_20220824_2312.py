# Generated by Django 2.2.19 on 2022-08-24 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveIntegerField(verbose_name='Время приготовления блюда'),
        ),
        migrations.AlterField(
            model_name='recipeingredientamount',
            name='amount',
            field=models.PositiveIntegerField(verbose_name='Количество'),
        ),
    ]