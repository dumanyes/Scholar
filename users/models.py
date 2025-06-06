import os
import sys
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from cities_light.models import Country, City
from datetime import date
from projects.models import Category
from django.db.models.signals import post_save
from django.dispatch import receiver


class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    icon = models.ImageField(upload_to='university_icons/', blank=True, null=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_online = models.DateTimeField(blank=True, null=True)

    # Basic Information
    orcid_id = models.CharField(max_length=19, blank=True, null=True, unique=True)
    avatar = models.ImageField(default='default-avatar.png', upload_to='profile_images')
    bio = models.TextField(blank=True, default="No bio available.")
    birthdate = models.DateField(blank=True, null=True)  # Added birthdate field

    university = models.ForeignKey(University, blank=True, null=True, on_delete=models.SET_NULL)

    # Professional Details
    skills = models.ManyToManyField('projects.Skill', blank=True, related_name='users')
    categories = models.ManyToManyField(Category, blank=True, related_name='profiles')

    organization = models.CharField(max_length=255, blank=True, default="Independent Researcher")
    position = models.CharField(max_length=255, blank=True, default="Member")

    # Contact & Links
    linkedin = models.URLField(blank=True, default="")
    github = models.URLField(blank=True, default="")
    google_scholar = models.URLField(blank=True, default="")
    telegram = models.CharField(max_length=100, blank=True, default="")

    telegram_chat_id = models.BigIntegerField(null=True, blank=True)

    # Location
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    # Platform Metrics
    date_joined = models.DateTimeField(default=timezone.now)
    reputation = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    # Updated field to prevent symmetrical ManyToMany warning
    related_projects = models.ManyToManyField('self', symmetrical=False, blank=True)

    allow_project_invites = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    notify_on_application = models.BooleanField(default=True)
    notify_on_application_status_change = models.BooleanField(default=True)
    notify_on_chat_message = models.BooleanField(default=True)
    # preferred_language = models.CharField(max_length=10, choices=[
    #     ('en', 'English'),
    #     ('ru', 'Русский'),
    #     ('kk', 'Қазақша'),
    # ], default='en')

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar and self.avatar.name:
            avatar_path = self.avatar.path

            if not os.path.exists(avatar_path):
                print(f"Avatar file not found at: {avatar_path}")
                # Set to default avatar if file is missing
                self.avatar = 'default-avatar.png'
                super().save(update_fields=['avatar'])
                return

            try:
                img = Image.open(avatar_path)
                if img.width > 300 or img.height > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size, Image.ANTIALIAS)
                    img.save(avatar_path, quality=95)
            except Exception as e:
                print(f"Error processing avatar image: {e}")

    @property
    def avatar_url(self):
        if self.avatar and os.path.exists(self.avatar.path):
            return self.avatar.url
        return settings.MEDIA_URL + "default-avatar.png"

    @property
    def location(self):
        if self.city and self.country:
            return f"{self.city.name}, {self.country.name}"
        return "Location not specified"

    @property
    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return
    if created and not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        return
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except Profile.DoesNotExist:
        pass