from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from cities_light.models import Country, City
from datetime import date

from projects.models import Category


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
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField(blank=True, default="No bio available.")
    birthdate = models.DateField(blank=True, null=True)  # Added birthdate field

    university = models.ForeignKey(University, blank=True, null=True, on_delete=models.SET_NULL)

    # Professional Details
    # Now referencing the Skill and Interest models from projects app.
    skills = models.ManyToManyField('projects.Skill', blank=True, related_name='users')
    categories = models.ManyToManyField(Category, blank=True, related_name='profiles')

    organization = models.CharField(max_length=255, blank=True, default="Independent Researcher")
    position = models.CharField(max_length=255, blank=True, default="Member")

    # Contact & Links
    linkedin = models.URLField(blank=True, default="")
    github = models.URLField(blank=True, default="")
    google_scholar = models.URLField(blank=True, default="")
    telegram = models.CharField(max_length=100, blank=True, default="")

    # Location
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    # Platform Metrics
    date_joined = models.DateTimeField(default=timezone.now)
    reputation = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    # Updated field to prevent symmetrical ManyToMany warning
    related_projects = models.ManyToManyField('self', symmetrical=False, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.width > 300 or img.height > 300:
                output_size = (300, 300)
                img.thumbnail(output_size, Image.ANTIALIAS)  # Maintain quality
                img.save(self.avatar.path, quality=95)  # Save with high quality

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
        return None  # Return None if birthdate is not provided
