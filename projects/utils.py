"""
Utility functions for Projects app
"""

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import math


def calculate_project_urgency(deadline):
    """
    Calculate urgency level based on deadline
    Returns: 'urgent', 'high', 'medium', or 'low'
    """
    if not deadline:
        return 'medium'

    days_until_deadline = (deadline - timezone.now().date()).days

    if days_until_deadline <= 3:
        return 'urgent'
    elif days_until_deadline <= 7:
        return 'high'
    elif days_until_deadline <= 14:
        return 'medium'
    else:
        return 'low'


def format_currency(amount):
    """
    Format currency in Kenyan Shillings
    """
    if amount is None:
        return "KES 0"

    if amount >= 1000000:
        return f"KES {amount / 1000000:.1f}M"
    elif amount >= 1000:
        return f"KES {amount / 1000:.1f}K"
    else:
        return f"KES {amount:,.0f}"


def calculate_artisan_score(artisan_profile):
    """
    Calculate overall score for artisan based on various factors
    """
    score = 0

    # Rating weight: 40%
    score += (artisan_profile.rating or 0) * 40 / 5

    # Completed projects weight: 30%
    project_score = min(artisan_profile.completed_projects or 0, 50)  # Cap at 50 projects
    score += (project_score / 50) * 30

    # Response rate weight: 20%
    score += (artisan_profile.response_rate or 0) * 20 / 100

    # Verification bonus: 10%
    if artisan_profile.is_verified:
        score += 10

    return round(score, 1)


def estimate_project_duration(timeline_string):
    """
    Estimate project duration in days from timeline string
    """
    if not timeline_string:
        return 30  # Default 30 days

    timeline = timeline_string.lower()

    if 'day' in timeline:
        # Extract number of days
        try:
            days = int(''.join(filter(str.isdigit, timeline.split('day')[0])))
            return days
        except:
            return 7  # Default 7 days

    elif 'week' in timeline:
        try:
            weeks = int(''.join(filter(str.isdigit, timeline.split('week')[0])))
            return weeks * 7
        except:
            return 14  # Default 2 weeks

    elif 'month' in timeline:
        try:
            months = int(''.join(filter(str.isdigit, timeline.split('month')[0])))
            return months * 30
        except:
            return 30  # Default 30 days

    else:
        return 30  # Default 30 days


def generate_project_code(user_id, timestamp):
    """
    Generate unique project code
    Format: MJ-{user_id}{timestamp}{random}
    """
    import random
    from datetime import datetime

    timestamp_str = datetime.now().strftime("%y%m%d%H%M")
    random_str = str(random.randint(100, 999))

    return f"MJ-{user_id}{timestamp_str}{random_str}"


def validate_bid_amount(amount, project):
    """
    Validate if bid amount is reasonable for the project
    """
    if amount < project.budget_min * Decimal('0.5'):
        return False, "Bid is too low compared to minimum budget"

    if amount > project.budget_max * Decimal('1.5'):
        return False, "Bid is too high compared to maximum budget"

    # Check if amount is within 30% of average bid if exists
    avg_bid = project.bids.aggregate(avg=models.Avg('amount'))['avg']
    if avg_bid and abs(amount - avg_bid) / avg_bid > Decimal('0.3'):
        return True, "Bid is significantly different from average bids"

    return True, "Bid amount is reasonable"


def get_recommended_projects(user, limit=5):
    """
    Get recommended projects for a user based on their profile
    """
    from .models import Project
    from users.models import ArtisanProfile

    if not user.is_authenticated:
        return Project.objects.filter(status='posted')[:limit]

    if user.profile.user_type == 'artisan':
        try:
            artisan_profile = ArtisanProfile.objects.get(user=user)
            # Recommend projects in same trade/category
            return Project.objects.filter(
                status='posted',
                category=artisan_profile.trade
            ).exclude(
                bids__artisan=user
            ).order_by('-posted_at')[:limit]
        except ArtisanProfile.DoesNotExist:
            pass

    # For homeowners, show popular projects
    return Project.objects.filter(
        status='posted'
    ).annotate(
        bid_count=models.Count('bids')
    ).order_by('-bid_count', '-posted_at')[:limit]