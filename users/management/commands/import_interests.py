# myapp/management/commands/import_interests.py
import csv
from django.core.management.base import BaseCommand
from users.models import Interest
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Import hobbies (interests) from CSV'

    def handle(self, *args, **kwargs):
        # Path to your CSV file
        csv_file_path = 'datas/hobbies.csv'

        try:
            with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)

                # Loop through each row in the CSV
                for row in csv_reader:
                    # Check if the 'HOBBIES' column exists in the CSV row
                    if 'HOBBIES' in row:
                        interest_name = row['HOBBIES']  # Adjusted to 'HOBBIES' (uppercase)
                    else:
                        self.stdout.write(self.style.WARNING(f"Skipping row with missing 'HOBBIES' column: {row}"))
                        continue  # Skip this row if the column is missing

                    # If you want to associate the interest with a specific user, for example, the first user
                    user = User.objects.first()  # Modify this to use the appropriate user

                    # Create the interest if it doesn't already exist
                    Interest.objects.get_or_create(
                        name=interest_name,
                        created_by=user,  # Replace with the desired user
                        approved=True  # Set based on your use case
                    )

                self.stdout.write(self.style.SUCCESS(f'Interests imported successfully from {csv_file_path}!'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
