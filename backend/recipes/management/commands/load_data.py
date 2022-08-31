import csv
import os

from django.core.management.base import BaseCommand
from backend.settings import BASE_DIR
from recipes.models import Ingredient

FILE = os.path.join(BASE_DIR, 'data', 'ingredients.csv')


class Command(BaseCommand):
    help = 'Load ingredients'

    def handle(self, *args, **options):
        table = csv.reader(
            open(FILE, encoding='utf-8'), delimiter=','
        )
        Ingredient.objects.bulk_create(
            Ingredient(
                name=row[0],
                measurement_unit=row[1]
            ) for row in list(table)
        )
