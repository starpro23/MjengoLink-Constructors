"""
Signal handlers for Users app
Automatically creates user profiles and handles related actions
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, ArtisanProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile when a new User is created
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile when User is saved
    """
    instance.profile.save()

@receiver(post_save, sender=ArtisanProfile)
def update_user_profile_stats(sender, instance, created, **kwargs):
    """
    Update user profile stats when artisan profile is updated
    """
    if not created:
        # Update user's profile with artisan stats if needed
        user_profile = instance.user.profile
        # Add any stats updates here as needed
        user_profile.save()