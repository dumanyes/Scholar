# Generated by Django 4.2.18 on 2025-02-22 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0016_interestscategory_skillscategory_and_more"),
        ("users", "0010_profile_birthdate"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="skill",
            name="created_by",
        ),
        migrations.AlterField(
            model_name="profile",
            name="interests",
            field=models.ManyToManyField(blank=True, to="projects.interest"),
        ),
        migrations.AlterField(
            model_name="profile",
            name="skills",
            field=models.ManyToManyField(
                blank=True, related_name="users", to="projects.skill"
            ),
        ),
        migrations.DeleteModel(
            name="Interest",
        ),
        migrations.DeleteModel(
            name="Skill",
        ),
    ]
