from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db import connection, OperationalError
from .models import Profile

User = get_user_model()

def profile_table_exists():
    try:
        return "users_profile" in connection.introspection.table_names()
    except OperationalError:
        return False

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if profile_table_exists():
            try:
                Profile.objects.get_or_create(user=instance)
            except Exception:
                pass

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if profile_table_exists():
        try:
            instance.profile.save()
        except (AttributeError, KeyError, OperationalError):
            pass
