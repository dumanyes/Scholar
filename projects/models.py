from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError

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


class MaxWordsValidator:
    """
    Validator that ensures a given text does not exceed a maximum number of words.
    """

    def __init__(self, max_words):
        self.max_words = max_words

    def __call__(self, value):
        if value:
            words = value.split()
            if len(words) > self.max_words:
                raise ValidationError(
                    f"Количество слов не должно превышать {self.max_words}. Сейчас {len(words)} слов."
                )

    def __eq__(self, other):
        return isinstance(other, MaxWordsValidator) and self.max_words == other.max_words

    def deconstruct(self):
        return (
            'projects.models.MaxWordsValidator',
            [self.max_words],
            {}
        )


# -------------------------------
# Общая категория для проектов
# -------------------------------
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# -------------------------------
# Иерархия навыков
# -------------------------------
class SkillsCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class SkillsSubCategory(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(SkillsCategory, on_delete=models.CASCADE, related_name='subcategories')

    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subcategory = models.ForeignKey(SkillsSubCategory, on_delete=models.CASCADE, related_name='skills')

    def __str__(self):
        return f"{self.name} ({self.subcategory.name} - {self.subcategory.category.name})"


# -------------------------------
# Иерархия интересов
# -------------------------------
class InterestsCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class InterestsSubCategory(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(InterestsCategory, on_delete=models.CASCADE, related_name='subcategories')

    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subcategory = models.ForeignKey(InterestsSubCategory, on_delete=models.CASCADE, related_name='interests')

    def __str__(self):
        return f"{self.name} ({self.subcategory.name} - {self.subcategory.category.name})"


# -------------------------------
# New Models: Languages and Required Roles
# -------------------------------
class Language(models.Model):
    """
    Represents a language relevant to a project.
    Can be used for programming languages (e.g., Python, JavaScript) or natural languages.
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return self.name


class RequiredRole(models.Model):
    """
    Represents a role required for a project, such as 'Designer', 'Developer', etc.
    Using a separate model helps manage and query these roles efficiently.
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Required Role"
        verbose_name_plural = "Required Roles"

    def __str__(self):
        return self.name


# -------------------------------
# Проект и связанные модели
# -------------------------------
class Project(models.Model):
    category = models.ManyToManyField(Category, blank=True)
    title = models.CharField(
        max_length=200,
        default='',
        validators=[MaxWordsValidator(20)]
    )
    description = models.TextField(
        default='',
        validators=[MaxWordsValidator(250)]
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        default=get_default_owner
    )
    created_at = models.DateTimeField(default=timezone.now)
    skills_required = models.ManyToManyField(Skill, blank=True, help_text="Select required skills")
    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    project_link = models.URLField(blank=True, null=True)
    project_mission = models.TextField(
        blank=True,
        null=True,
        validators=[MaxWordsValidator(70)]
    )
    project_objectives = models.TextField(
        blank=True,
        null=True,
        validators=[MaxWordsValidator(150)]
    )
    # Updated languages and required_roles fields as many-to-many relationships.
    languages = models.ManyToManyField(
        Language, blank=True,
        help_text="Select languages relevant to the project (e.g., Python, Spanish, etc.)"
    )
    required_roles = models.ManyToManyField(
        RequiredRole, blank=True,
        help_text="Select roles required for the project (e.g., Designer, Developer, etc.)"
    )
    # -------------------------------
    # Metrics fields to track engagement and performance
    # -------------------------------
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the project page has been viewed."
    )
    application_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of applications received for this project."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Research Project'
        verbose_name_plural = 'Research Projects'

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.pk is not None and self.category.count() > 5:
            raise ValidationError("You can select at most 5 categories.")

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})

    def toggle_active_status(self):
        self.is_active = not self.is_active
        self.save()
        return self.is_active

    @property
    def skills_list(self):
        return [skill.name for skill in self.skills_required.all()]

    def get_skill_match(self, user):
        """
        Calculates the match score between the project's required skills and the user's skills.
        If no required skills are set, returns 100.
        """
        if not user.is_authenticated or not hasattr(user, 'profile'):
            return 0
        required_skills = {skill.name.lower() for skill in self.skills_required.all()}
        if not required_skills:
            return 100
        user_skills = {skill.name.lower() for skill in user.profile.skills.all()}
        if not user_skills:
            return 0
        match_count = len(required_skills & user_skills)
        return round((match_count / len(required_skills)) * 100)

    @property
    def popularity_score(self):
        """
        Calculates a simple popularity score for the project.
        This metric can be used to rank projects by engagement.
        For example, we can weight each application more heavily than a view.
        """
        # Example: each application is weighted 10 times more than a view.
        return self.application_count * 10 + self.view_count


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
    contribution = models.TextField(
        blank=True,
        help_text="Опишите, как вы планируете участвовать в проекте."
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

    @property
    def matching_score(self):
        """
        Returns a match score for the candidate with respect to the project,
        calculated via the project's get_skill_match method.
        """
        return self.project.get_skill_match(self.applicant)

class FavoriteProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_projects')
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} - {self.project.title}"


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
        # Either remove the method entirely or just return the raw content
        return self.content


class ChatFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_folders")
    name = models.CharField(max_length=100)
    chats = models.ManyToManyField(ChatRoom, blank=True, related_name="folders")

    def __str__(self):
        return self.name

class ProjectInvitation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'invited_user')

    def __str__(self):
        return f"Invitation for {self.invited_user.username} to project {self.project.title}"

class PinnedProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')
        ordering = ['-pinned_at']
