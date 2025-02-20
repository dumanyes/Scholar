# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

User = get_user_model()

def get_default_owner():
    """Get or create a default owner user"""
    user, _ = User.objects.get_or_create(
        username='default_owner',
        defaults={
            'is_active': False,
            'password': 'unusable_password'
        }
    )
    return user.id

class Project(models.Model):
    CATEGORY_CHOICES = [
        ('AI', 'Artificial Intelligence'),
        ('EDU', 'Education'),
        ('BIO', 'Biology'),
        ('CS', 'Computer Science'),
    ]

    title = models.CharField(max_length=200, default='Untitled Project')
    description = models.TextField(default='No description provided')
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='AI'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        default=get_default_owner  # Add default value
    )
    created_at = models.DateTimeField(default=timezone.now)
    skills_required = models.CharField(
        max_length=200,
        default='No specific skills required',
        help_text="Comma-separated list of skills"
    )
    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    project_link = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Research Project'
        verbose_name_plural = 'Research Projects'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})

    def toggle_active_status(self):
        self.is_active = not self.is_active
        self.save()
        return self.is_active

    @property
    def skills_list(self):
        return [skill.strip() for skill in self.skills_required.split(',')]

    # projects/models.py
    def get_skill_match(self, user):
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return 0

        required_skills = {s.strip().lower() for s in self.skills_required.split(',') if s.strip()}
        if not required_skills:
            return 100

        user_skills = {s.name.lower() for s in user.profile.skills.all()}
        if not user_skills:
            return 0

        match_count = len(required_skills & user_skills)
        return round((match_count / len(required_skills)) * 100)




class ProjectApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected')
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_applications'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    message = models.TextField(
        blank=True,
        help_text="Optional message to the project owner"
    )

    class Meta:
        unique_together = ('project', 'applicant')
        ordering = ['-applied_at']
        verbose_name = 'Project Application'
        verbose_name_plural = 'Project Applications'

    def __str__(self):
        return f"{self.applicant} → {self.project} ({self.status})"

    def get_status_color(self):
        status_colors = {
            'PENDING': 'warning',
            'ACCEPTED': 'success',
            'REJECTED': 'danger'
        }
        return status_colors.get(self.status, 'secondary')

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}"

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat between {', '.join([user.username for user in self.participants.all()])}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"