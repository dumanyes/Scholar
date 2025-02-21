# Generated by Django 4.2.18 on 2025-02-10 15:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0008_researchsection_delete_projectsection"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectApplication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("applied_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("ACCEPTED", "Accepted"),
                            ("REJECTED", "Rejected"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "applicant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Project Application",
                "verbose_name_plural": "Project Applications",
            },
        ),
        migrations.RemoveField(
            model_name="comment",
            name="project",
        ),
        migrations.RemoveField(
            model_name="comment",
            name="user",
        ),
        migrations.RemoveField(
            model_name="researchsection",
            name="project",
        ),
        migrations.RemoveField(
            model_name="project",
            name="abstract",
        ),
        migrations.RemoveField(
            model_name="project",
            name="authors",
        ),
        migrations.RemoveField(
            model_name="project",
            name="citation",
        ),
        migrations.RemoveField(
            model_name="project",
            name="citation_link",
        ),
        migrations.RemoveField(
            model_name="project",
            name="pdf_file",
        ),
        migrations.RemoveField(
            model_name="project",
            name="publish_date",
        ),
        migrations.RemoveField(
            model_name="project",
            name="related_projects",
        ),
        migrations.RemoveField(
            model_name="project",
            name="tags",
        ),
        migrations.AddField(
            model_name="project",
            name="category",
            field=models.CharField(
                choices=[
                    ("AI", "Artificial Intelligence"),
                    ("EDU", "Education"),
                    ("BIO", "Biology"),
                    ("CS", "Computer Science"),
                ],
                default="AI",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="project",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="project",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="skills_required",
            field=models.CharField(
                default="No specific skills required", max_length=200
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="description",
            field=models.TextField(default="No description provided"),
        ),
        migrations.AlterField(
            model_name="project",
            name="title",
            field=models.CharField(default="Untitled Project", max_length=200),
        ),
        migrations.DeleteModel(
            name="Citation",
        ),
        migrations.DeleteModel(
            name="Comment",
        ),
        migrations.DeleteModel(
            name="ResearchSection",
        ),
        migrations.DeleteModel(
            name="Tag",
        ),
        migrations.AddField(
            model_name="projectapplication",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applications",
                to="projects.project",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="projectapplication",
            unique_together={("project", "applicant")},
        ),
    ]
