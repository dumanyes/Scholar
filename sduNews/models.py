from django.db import models

class Journal(models.Model):
    title = models.CharField(max_length=255)
    journal_url = models.URLField()
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    view_link = models.URLField(blank=True, null=True)
    current_issue_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title
