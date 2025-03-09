import csv
import os
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import University

CSV_FILE_PATH = os.path.join(settings.BASE_DIR, "datas/list_of_univs.csv")

class Command(BaseCommand):
    help = 'Imports universities from a CSV file with actual icon URLs'

    def handle(self, *args, **kwargs):
        with open(CSV_FILE_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row.get("name", "").strip()
                if not name:
                    continue  # Skip if no name

                # Use get_or_create to avoid duplicates
                university, created = University.objects.get_or_create(name=name)
                if created:
                    icon_url = row.get("icon_url", "").strip()
                    if icon_url:
                        try:
                            response = requests.get(icon_url)
                            if response.status_code == 200:
                                # Use the basename from the URL as the file name
                                file_name = os.path.basename(icon_url)
                                university.icon.save(file_name, ContentFile(response.content), save=True)
                                self.stdout.write(self.style.SUCCESS(f"Added: {name} with icon from {icon_url}"))
                            else:
                                self.stdout.write(self.style.WARNING(f"Failed to download icon for {name}. Status code: {response.status_code}"))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Error downloading icon for {name}: {e}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"No icon URL provided for {name}"))
                else:
                    self.stdout.write(f"Skipped (already exists): {name}")
