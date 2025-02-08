import csv
from django.core.management.base import BaseCommand
from users.models import Skill


class Command(BaseCommand):
    help = 'Import skills from CSV file'

    def handle(self, *args, **kwargs):
        file_path = 'datas/skills.csv'

        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # Skip header row if it exists
                print(f"Header: {header}")

                count = 0
                for row in reader:
                    print(f"Row: {row}")  # Debugging: Print each row
                    skill_name = row[0].strip()
                    if skill_name:
                        skill, created = Skill.objects.get_or_create(name=skill_name)
                        print(f"Added: {skill.name}, Created: {created}")  # Debug output
                        count += 1

                self.stdout.write(self.style.SUCCESS(f'Skills imported successfully! {count} new skills added.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
