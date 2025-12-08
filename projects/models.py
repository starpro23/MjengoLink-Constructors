from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Project(models.Model):
    """Construction project posted by homeowners"""
    CATEGORY_CHOICES = [
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
        ('renovation', 'Renovation'),
        ('new_construction', 'New Construction'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted - Accepting Bids'),
        ('bidding_closed', 'Bidding Closed'),
        ('assigned', 'Assigned to Artisan'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]

    URGENCY_CHOICES = [
        ('low', 'Low - Within 1 month'),
        ('medium', 'Medium - Within 2 weeks'),
        ('high', 'High - Within 1 week'),
        ('urgent', 'Urgent - Within 3 days'),
    ]

    # TO this (correct - each field on its own line):
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    exact_address = models.TextField(blank=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    preferred_timeline = models.CharField(max_length=100, help_text="e.g., 2 weeks, 1 month")
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Project details
    area_size = models.CharField(max_length=100, blank=True, help_text="e.g., 100 sq ft, 3 bedrooms")
    materials_provided = models.BooleanField(default=False)
    special_requirements = models.TextField(blank=True)

    # Dates
    posted_at = models.DateTimeField(auto_now_add=True)
    bidding_deadline = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_projects')
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_timeline = models.CharField(max_length=100, blank=True)

    # Statistics
    view_count = models.IntegerField(default=0)
    bid_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    @property
    def budget_range(self):
        return f"KES {self.budget_min:,} - KES {self.budget_max:,}"

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['homeowner', 'status']),
        ]


class ProjectImage(models.Model):
    """Images attached to projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='project_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.project.title}"

    class Meta:
        ordering = ['-is_primary', 'uploaded_at']


class Bid(models.Model):
    """Bids submitted by artisans for projects"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('expired', 'Expired'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bids')
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    timeline = models.CharField(max_length=100, help_text="e.g., 10 days, 2 weeks")
    proposal = models.TextField()
    notes = models.TextField(blank=True, help_text="Additional notes or conditions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bid: {self.artisan.username} - KES {self.amount:,}"

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['project', 'artisan']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['artisan', 'status']),
        ]


class ProjectMessage(models.Model):
    """Messages between homeowners and artisans"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.message[:50]}"

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['project', 'created_at']),
            models.Index(fields=['sender', 'receiver', 'created_at']),
        ]


class ProjectMilestone(models.Model):
    """Milestones for project progress tracking"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved by Homeowner'),
        ('paid', 'Paid'),
    ], default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Milestone: {self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['due_date', 'created_at']


class ProjectReview(models.Model):
    """Reviews after project completion"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    is_verified = models.BooleanField(default=False, help_text="Verified as genuine review")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review: {self.reviewer.username} → {self.reviewee.username}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'reviewer']


