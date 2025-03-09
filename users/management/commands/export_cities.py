import json
from django.core.management.base import BaseCommand
from cities_light.models import City

class Command(BaseCommand):
    help = "Export cities to a JSON file"

    def handle(self, *args, **kwargs):
        cities = City.objects.values("id", "name", "country_id")
        data = {"cities": list(cities)}

        with open("cities.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(self.style.SUCCESS("Successfully exported cities to cities.json"))

