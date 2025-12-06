"""
Signals for Projects app
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from .models import Project, Bid, ProjectReview, ProjectMilestone
from users.models import ArtisanProfile

@receiver(post_save, sender=Project)
def update_project_status_on_save(sender, instance, created, **kwargs):
    """
    Update project status based on milestones and other factors
    """
    if not created and instance.status in ['assigned', 'in_progress']:
        # Check if all milestones are completed
        milestones = instance.milestones.all()
        if milestones.exists():
            completed_milestones = milestones.filter(status='completed').count()
            if completed_milestones == milestones.count():
                instance.status = 'completed'
                instance.completed_at = timezone.now()
                instance.save(update_fields=['status', 'completed_at'])

@receiver(post_save, sender=Bid)
def update_project_bid_count(sender, instance, created, **kwargs):
    """
    Update bid count on project when bid is created or deleted
    """
    if created:
        instance.project.bid_count += 1
        instance.project.save(update_fields=['bid_count'])

@receiver(post_delete, sender=Bid)
def decrement_project_bid_count(sender, instance, **kwargs):
    """
    Decrease bid count when bid is deleted
    """
    try:
        instance.project.bid_count -= 1
        if instance.project.bid_count < 0:
            instance.project.bid_count = 0
        instance.project.save(update_fields=['bid_count'])
    except Project.DoesNotExist:
        pass  # Project was deleted

@receiver(post_save, sender=ProjectReview)
def update_artisan_rating(sender, instance, created, **kwargs):
    """
    Update artisan rating when a new review is added
    """
    if created and instance.review_type == 'homeowner':
        try:
            artisan_profile = ArtisanProfile.objects.get(user=instance.reviewee)
            artisan_profile.update_rating()
            artisan_profile.save()
        except ArtisanProfile.DoesNotExist:
            pass

@receiver(pre_save, sender=Project)
def set_posted_date(sender, instance, **kwargs):
    """
    Set posted_at date when project status changes to 'posted'
    """
    if instance.pk:
        try:
            old_instance = Project.objects.get(pk=instance.pk)
            if old_instance.status != 'posted' and instance.status == 'posted':
                instance.posted_at = timezone.now()
        except Project.DoesNotExist:
            pass
    elif instance.status == 'posted':
        instance.posted_at = timezone.now()

@receiver(pre_save, sender=ProjectMilestone)
def update_milestone_status(sender, instance, **kwargs):
    """
    Update milestone completion date when marked as completed
    """
    if instance.pk:
        try:
            old_instance = ProjectMilestone.objects.get(pk=instance.pk)
            if old_instance.status != 'completed' and instance.status == 'completed':
                instance.completed_at = timezone.now()
        except ProjectMilestone.DoesNotExist:
            pass
    elif instance.status == 'completed':
        instance.completed_at = timezone.now()

@receiver(post_save, sender=ProjectMilestone)
def handle_milestone_payment(sender, instance, created, **kwargs):
    """
    Handle payment logic when milestone is marked as completed
    """
    if instance.status == 'completed' and not instance.paid:
        # Here you would integrate with payment system
        # For now, just mark as paid if it's the final milestone
        project = instance.project
        if project.milestones.filter(status='completed').count() == project.milestones.count():
            # All milestones completed, mark project as paid
            project.is_paid = True
            project.save(update_fields=['is_paid'])
            instance.paid = True
            instance.save(update_fields=['paid'])