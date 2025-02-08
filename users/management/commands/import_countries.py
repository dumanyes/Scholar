import json
from django.core.management.base import BaseCommand
from cities_light.models import Country

class Command(BaseCommand):
    help = "Import countries and flags from a JSON file"

    def handle(self, *args, **kwargs):
        try:
            with open("countries.json", "r", encoding="utf-8") as f:
                countries_data = json.load(f)

            for country_data in countries_data:
                country_name = country_data.get("name", {}).get("common", "")
                country_alpha2 = country_data.get("cca2", "")
                country_flag = country_data.get("flags", {}).get("png", "")  # PNG flag URL

                if country_name and country_alpha2:
                    country, created = Country.objects.update_or_create(
                        code2=country_alpha2,
                        defaults={"name": country_name},
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"{'Added' if created else 'Updated'}: {country_name}")
                    )
                else:
                    self.stdout.write(self.style.WARNING(f"Skipping incomplete data: {country_data}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing countries: {e}"))

