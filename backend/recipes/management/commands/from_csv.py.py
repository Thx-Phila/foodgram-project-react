import csv

from django.conf import settings
from django.core.management import BaseCommand
from django.db.utils import IntegrityError
from recipes.models import Ingredient, Tag

TABLES = {
    Ingredient: 'ingredients.csv',
    Tag: 'tags.csv',
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            for model, csv_f in TABLES.items():
                with open(
                    f'{settings.BASE_DIR}/data/{csv_f}',
                    'r',
                    encoding='utf-8',
                ) as csv_file:
                    reader = csv.DictReader(csv_file)
                    model.objects.bulk_create(model(**data) for data in reader)
                print(f'  Importing data from file {csv_f}... OK')
            print()
            print(
                '======================================')
            self.stdout.write(
                self.style.SUCCESS(
                    'The all data from .csv-files are imported.')
            )
        except IntegrityError:
            print('Данная запись уже есть в базе данных')
