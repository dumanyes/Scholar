# Generated by Django 4.2.18 on 2025-02-22 13:36

from django.db import migrations, models
import projects.models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0017_remove_interest_interests_category_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="description",
            field=models.TextField(
                default="", validators=[projects.models.MaxWordsValidator(250)]
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="title",
            field=models.CharField(
                default="",
                max_length=200,
                validators=[projects.models.MaxWordsValidator(20)],
            ),
        ),
    ]
