# Generated by Django 4.2.18 on 2025-02-23 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0019_language_requiredrole_project_application_count_and_more"),
        ("users", "0011_remove_skill_created_by_alter_profile_interests_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="interests",
        ),
        migrations.AddField(
            model_name="profile",
            name="categories",
            field=models.ManyToManyField(
                blank=True, related_name="profiles", to="projects.category"
            ),
        ),
    ]
