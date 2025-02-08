from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from cities_light.models import Country, City

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    icon = models.ImageField(upload_to='university_icons/', blank=True, null=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Information
    orcid_id = models.CharField(max_length=19, blank=True, null=True, unique=True)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField(blank=True, default="No bio available.")

    university = models.ForeignKey(University, blank=True, null=True, on_delete=models.SET_NULL)

    # Professional Details
    skills = models.ManyToManyField(Skill, blank=True)
    interests = models.ManyToManyField(Interest, blank=True)
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

    from PIL import Image

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
