# Generated by Django 4.2.18 on 2025-02-20 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_profile_university"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="birthdate",
            field=models.DateField(blank=True, null=True),
        ),
    ]
