# Generated by Django 4.2.18 on 2025-01-26 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_profile_bio"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="orcid_id",
            field=models.CharField(blank=True, max_length=19, null=True),
        ),
    ]
