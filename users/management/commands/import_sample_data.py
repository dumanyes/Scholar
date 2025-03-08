import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile, University  # adjust if needed
from projects.models import (
    Project, Category, Skill, Language, RequiredRole
)

class Command(BaseCommand):
    help = "Import sample users and projects from CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--users_csv',
            type=str,
            default='users_extended.csv',
            help='Path to the users CSV file (default: users_extended.csv)'
        )
        parser.add_argument(
            '--projects_csv',
            type=str,
            default='research_projects_extended.csv',
            help='Path to the projects CSV file (default: research_projects_extended.csv)'
        )

    def handle(self, *args, **options):
        users_csv = options['users_csv']
        projects_csv = options['projects_csv']

        self.stdout.write("Importing users...")
        self.import_users(users_csv)

        self.stdout.write("Importing projects...")
        self.import_projects(projects_csv)

        self.stdout.write(self.style.SUCCESS("Import completed successfully."))

    def import_users(self, csv_path):
        try:
            with open(csv_path, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    username = row.get('username')
                    email = row.get('email')
                    bio = row.get('bio', '')
                    birthdate_str = row.get('birthdate', '')

                    if not username:
                        self.stdout.write(self.style.WARNING("Skipping row with missing username"))
                        continue

                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={'email': email}
                    )
                    if created:
                        # Set a default password
                        user.set_password("password")
                        user.save()

                    # Ensure profile exists
                    profile, _ = Profile.objects.get_or_create(user=user)
                    profile.bio = bio
                    if birthdate_str:
                        try:
                            profile.birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f"Invalid birthdate for {username}: {birthdate_str}"))
                    profile.save()

                    self.stdout.write(self.style.SUCCESS(f"Imported user: {username}"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Users CSV not found at: {csv_path}"))

    def import_projects(self, csv_path):
        try:
            with open(csv_path, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get('title')
                    description = row.get('description', '')
                    mission = row.get('mission', '')
                    objectives = row.get('objectives', '')
                    link = row.get('link', '')
                    owner_username = row.get('owner')
                    categories_str = row.get('categories', '')
                    skills_str = row.get('required_skills', '')
                    languages_str = row.get('languages', '')
                    roles_str = row.get('required_roles', '')
                    is_active_str = row.get('is_active', 'True')

                    if not title or not owner_username:
                        self.stdout.write(self.style.WARNING("Skipping row due to missing title or owner"))
                        continue

                    try:
                        owner = User.objects.get(username=owner_username)
                    except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Owner {owner_username} not found. Skipping project: {title}"))
                        continue

                    # Create or update project
                    project, created = Project.objects.get_or_create(
                        title=title,
                        owner=owner,
                        defaults={
                            'description': description,
                            'project_mission': mission,
                            'project_objectives': objectives,
                            'project_link': link,
                            'is_active': is_active_str.lower() == 'true'
                        }
                    )
                    if not created:
                        project.description = description
                        project.project_mission = mission
                        project.project_objectives = objectives
                        project.project_link = link
                        project.is_active = is_active_str.lower() == 'true'
                        project.save()

                    # Process many-to-many fields:
                    self.assign_many_to_many(project, 'category', categories_str, Category)
                    self.assign_many_to_many(project, 'skills_required', skills_str, Skill)
                    self.assign_many_to_many(project, 'languages', languages_str, Language)
                    self.assign_many_to_many(project, 'required_roles', roles_str, RequiredRole)

                    self.stdout.write(self.style.SUCCESS(f"Imported project: {title}"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Projects CSV not found at: {csv_path}"))

    def assign_many_to_many(self, project, field_name, csv_value, model_class):
        """
        Helper function to assign a comma-separated CSV value to a many-to-many field.
        For each value in csv_value, get_or_create the object in model_class.
        """
        if csv_value.strip() == "":
            return
        items = [item.strip() for item in csv_value.split(",") if item.strip()]
        objects = []
        for item in items:
            obj, _ = model_class.objects.get_or_create(name=item)
            objects.append(obj)
        getattr(project, field_name).set(objects)
