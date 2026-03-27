# portal/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, App, UserAppAccess


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile instance when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    instance.profile.save()


@receiver(post_save, sender=User)
def assign_default_apps(sender, instance, created, **kwargs):
    """Assign default apps to new users."""
    if created:
        default_apps = App.objects.filter(is_default=True)
        for app in default_apps:
            UserAppAccess.objects.get_or_create(user=instance, app=app)

# NOTE: update_app_choices signal removed. ActivityLog.app is now a proper
# ForeignKey to App, so choices no longer need to be maintained manually.