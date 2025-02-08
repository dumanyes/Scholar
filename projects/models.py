from django.contrib.auth.models import User
from django.db import models

# Tag model for categorizing projects
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Project model for storing project details
class Project(models.Model):
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    description = models.TextField()
    publish_date = models.DateField()
    authors = models.ManyToManyField('auth.User', related_name='projects')
    pdf_file = models.FileField(upload_to='projects/pdfs/', null=True, blank=True)
    citation = models.TextField(null=True, blank=True)
    citation_link = models.URLField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='projects', blank=True)  # Corrected the related_name for Tag model
    related_projects = models.ManyToManyField('self', related_name='related_projects', blank=True)

    def __str__(self):
        return self.title

# ResearchSection model for storing different sections of a research paper
class ResearchSection(models.Model):
    project = models.ForeignKey(Project, related_name='research_sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.title

# Comment model for storing comments on projects
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.title}"

    class Meta:
        ordering = ['created_at']

# Citation model for storing citations related to projects
class Citation(models.Model):
    project = models.ForeignKey(Project, related_name='citations', on_delete=models.CASCADE)
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    journal_name = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    doi = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Citation for {self.project.title}"
