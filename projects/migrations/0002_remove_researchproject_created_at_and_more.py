# Generated by Django 4.2.18 on 2025-01-28 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="researchproject",
            name="created_at",
        ),
        migrations.AddField(
            model_name="researchproject",
            name="availability",
            field=models.CharField(
                choices=[("free", "Free Open"), ("restricted", "Need Access")],
                default="free",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="researchproject",
            name="comments",
            field=models.TextField(blank=True, default="No comments yet.", null=True),
        ),
        migrations.AddField(
            model_name="researchproject",
            name="partial_access_description",
            field=models.TextField(
                blank=True, default="No partial access available.", null=True
            ),
        ),
        migrations.AddField(
            model_name="researchproject",
            name="pdf_file",
            field=models.FileField(
                default="default.pdf", upload_to="research_projects/"
            ),
        ),
        migrations.AlterField(
            model_name="researchproject",
            name="description",
            field=models.TextField(default="No description provided."),
        ),
        migrations.AlterField(
            model_name="researchproject",
            name="title",
            field=models.CharField(default="Untitled Project", max_length=200),
        ),
    ]
