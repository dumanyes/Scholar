import csv
import os
from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import University

CSV_FILE_PATH = os.path.join(settings.BASE_DIR, "datas/list_of_univs.csv")
DEFAULT_ICON_PATH = os.path.join(settings.BASE_DIR, "media/default.jpg")

class Command(BaseCommand):
    help = 'Imports universities from a CSV file'

    def handle(self, *args, **kwargs):
        with open(CSV_FILE_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                name = row.get("name", "").strip()
                if not name:
                    continue  # Skip if no name

                university, created = University.objects.get_or_create(name=name)

                if created:
                    with open(DEFAULT_ICON_PATH, "rb") as icon_file:
                        university.icon.save("default.jpg", File(icon_file), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Added: {name}"))
                else:
                    self.stdout.write(f"Skipped (already exists): {name}")
