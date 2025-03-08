import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile
from projects.recommendation import recommend_projects_for_user

class Command(BaseCommand):
    help = "Generate a CSV file containing similarity scores for recommended projects for all users (or a specific user if provided)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Generate similarity CSV for a specific username. If omitted, generate for all users.",
        )
        parser.add_argument(
            "--top_n",
            type=int,
            default=5,
            help="Number of recommended projects per user (default is 5).",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        top_n = options.get("top_n")

        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{username}' not found."))
                return
        else:
            users = User.objects.all()

        output_file = "user_project_similarity.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["username", "project_title", "similarity"])
            for user in users:
                # Ensure the user has a profile; if not, create one.
                profile, created = Profile.objects.get_or_create(user=user)
                # Get top_n recommended projects for this user.
                try:
                    recommended = list(recommend_projects_for_user(user, top_n=top_n))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error generating recommendations for {user.username}: {e}"))
                    continue

                for project in recommended:
                    similarity = project.get_skill_match(user)
                    writer.writerow([user.username, project.title, similarity])
                    self.stdout.write(f"Wrote: {user.username}, {project.title}, {similarity}")
        self.stdout.write(self.style.SUCCESS(f"CSV file '{output_file}' generated successfully."))
