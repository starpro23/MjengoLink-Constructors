from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    """Extended user profile"""
    USER_TYPE_CHOICES = [
        ('homeowner', 'Homeowner'),
        ('artisan', 'Artisan'),
        ('admin', 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='homeowner')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats for dashboard
    total_projects = models.IntegerField(default=0)
    completed_projects = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        ordering = ['-created_at']


class ArtisanProfile(models.Model):
    """Additional details for artisans"""
    TRADE_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('masonry', 'Masonry'),
        ('carpentry', 'Carpentry'),
        ('painting', 'Painting'),
        ('welding', 'Welding'),
        ('roofing', 'Roofing'),
        ('tiling', 'Tiling'),
        ('landscaping', 'Landscaping'),
        ('interior_design', 'Interior Design'),
        ('plastering', 'Plastering'),
        ('metalwork', 'Metalwork'),
        ('glass_work', 'Glass Work'),
        ('flooring', 'Flooring'),
        ('fencing', 'Fencing'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artisan_profile')
    trade = models.CharField(max_length=50, choices=TRADE_CHOICES)
    experience_years = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    skills = models.TextField(blank=True, help_text="Comma-separated list of skills")
    certifications = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='verified_artisans')
    id_number = models.CharField(max_length=20, blank=True, help_text="National ID for verification")
    id_verified = models.BooleanField(default=False)

    # Performance metrics
    total_completed = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    response_time_hours = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_trade_display()}"

    class Meta:
        ordering = ['-is_verified', 'user__first_name']


class ArtisanDocument(models.Model):
    """Documents for artisan verification"""
    DOCUMENT_TYPES = [
        ('id_card', 'National ID Card'),
        ('passport', 'Passport'),
        ('certificate', 'Professional Certificate'),
        ('license', 'Business License'),
        ('portfolio', 'Portfolio'),
        ('reference', 'Reference Letter'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]

    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='artisan_documents/')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.artisan.username} - {self.get_document_type_display()}"

    class Meta:
        ordering = ['-uploaded_at']


class ArtisanPortfolioImage(models.Model):
    """Portfolio images for artisans"""
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_images')
    image = models.ImageField(upload_to='portfolio_images/')
    caption = models.CharField(max_length=200, blank=True)
    project_type = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    year_completed = models.IntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Portfolio: {self.artisan.username} - {self.caption[:50]}"

    class Meta:
        ordering = ['-uploaded_at']


class ArtisanReference(models.Model):
    """References for artisan verification"""
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='references')
    reference_name = models.CharField(max_length=100)
    reference_phone = models.CharField(max_length=20)
    reference_email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=100, help_text="e.g., Former Client, Employer")
    project_description = models.TextField(blank=True)
    contact_permission = models.BooleanField(default=False)
    contacted = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reference: {self.reference_name} for {self.artisan.username}"

    class Meta:
        ordering = ['-created_at']


# Signal handlers
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    instance.profile.save()


# Create admin models in users app

class AdminActionLog(models.Model):
    """Log of admin actions for audit trail"""
    ACTION_TYPES = [
        ('user_verification', 'User Verification'),
        ('document_approval', 'Document Approval'),
        ('dispute_resolution', 'Dispute Resolution'),
        ('user_suspension', 'User Suspension'),
        ('content_moderation', 'Content Moderation'),
        ('payment_release', 'Payment Release'),
        ('platform_update', 'Platform Update'),
        ('other', 'Other'),
    ]

    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='admin_actions')
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.get_action_type_display()} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
        ]


class PlatformMetric(models.Model):
    """Platform metrics for admin dashboard"""
    METRIC_TYPES = [
        ('verification_turnaround', 'Verification Turnaround Time'),
        ('dispute_resolution', 'Dispute Resolution Rate'),
        ('platform_trust', 'Platform Trust Score'),
        ('user_retention', 'User Retention Rate'),
        ('transaction_volume', 'Transaction Volume'),
        ('active_users', 'Active Users'),
        ('new_signups', 'New Signups'),
        ('project_completion', 'Project Completion Rate'),
        ('fraud_prevention', 'Fraud Prevention Rate'),
        ('user_satisfaction', 'User Satisfaction Score'),
    ]

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    value = models.FloatField()
    target_value = models.FloatField(null=True, blank=True)
    period = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ])
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value}"

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', 'recorded_at']),
        ]
        unique_together = ['metric_type', 'period', 'recorded_at']



