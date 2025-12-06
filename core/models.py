from django.db import models
from django.contrib.auth.models import User


class SiteSetting(models.Model):
    """Site-wide settings"""
    site_name = models.CharField(max_length=100, default='MjengoLink')
    tagline = models.CharField(max_length=200, default='Find Trusted Construction Artisans')
    contact_email = models.EmailField(default='info@mjengolink.com')
    contact_phone = models.CharField(max_length=20, default='+254 700 000 000')
    address = models.TextField(default='Nairobi, Kenya')
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    newsletter_subscription = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"


class ContactMessage(models.Model):
    """Contact form submissions"""
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('artisan', 'Become an Artisan'),
        ('business', 'Business Partnership'),
        ('feedback', 'Feedback & Suggestions'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"

    class Meta:
        ordering = ['-created_at']


class Testimonial(models.Model):
    """Client testimonials for homepage"""
    client_name = models.CharField(max_length=100)
    client_location = models.CharField(max_length=100)
    client_type = models.CharField(max_length=50, choices=[
        ('homeowner', 'Homeowner'),
        ('artisan', 'Artisan'),
    ])
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    client_photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.client_name}"

    class Meta:
        ordering = ['-created_at']


class FAQ(models.Model):
    """Frequently Asked Questions"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('homeowners', 'For Homeowners'),
        ('artisans', 'For Artisans'),
        ('payments', 'Payments'),
        ('safety', 'Safety & Trust'),
    ]

    question = models.CharField(max_length=200)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ['order', 'question']


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers"""
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-subscribed_at']


