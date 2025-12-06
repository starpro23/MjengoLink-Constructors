"""
Signal Handlers for Core App
Contains signal receivers for:
- Automatically sending emails on contact form submission
- Sending welcome emails to newsletter subscribers
- Updating site statistics
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import ContactMessage, NewsletterSubscriber, SiteSetting


@receiver(post_save, sender=ContactMessage)
def send_contact_confirmation_email(sender, instance, created, **kwargs):
    """
    Send confirmation email when contact form is submitted
    """
    if created and settings.DEBUG:  # Only in development for now
        try:
            site_settings = SiteSetting.objects.first()
            if site_settings:
                subject = f"Thank you for contacting {site_settings.site_name}"

                # Render HTML email template
                html_message = render_to_string('emails/contact_confirmation.html', {
                    'name': instance.name,
                    'subject': instance.subject,
                    'message': instance.message,
                    'site_name': site_settings.site_name,
                    'contact_email': site_settings.contact_email,
                    'contact_phone': site_settings.contact_phone,
                })

                plain_message = strip_tags(html_message)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=site_settings.contact_email,
                    recipient_list=[instance.email],
                    html_message=html_message,
                    fail_silently=True,
                )

                # Also send notification to admin
                admin_subject = f"New Contact Form Submission: {instance.subject}"
                admin_html = render_to_string('emails/contact_admin_notification.html', {
                    'contact': instance,
                    'site_name': site_settings.site_name,
                })
                admin_plain = strip_tags(admin_html)

                send_mail(
                    subject=admin_subject,
                    message=admin_plain,
                    from_email=site_settings.contact_email,
                    recipient_list=[site_settings.contact_email],
                    html_message=admin_html,
                    fail_silently=True,
                )
        except Exception as e:
            # Log error but don't break the application
            print(f"Error sending contact confirmation email: {e}")


@receiver(post_save, sender=NewsletterSubscriber)
def send_welcome_newsletter_email(sender, instance, created, **kwargs):
    """
    Send welcome email when someone subscribes to newsletter
    """
    if created and settings.DEBUG:  # Only in development for now
        try:
            site_settings = SiteSetting.objects.first()
            if site_settings and instance.is_active:
                subject = f"Welcome to {site_settings.site_name} Newsletter!"

                html_message = render_to_string('emails/newsletter_welcome.html', {
                    'email': instance.email,
                    'site_name': site_settings.site_name,
                    'unsubscribe_url': '#',  # Would be actual URL in production
                })

                plain_message = strip_tags(html_message)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=site_settings.contact_email,
                    recipient_list=[instance.email],
                    html_message=html_message,
                    fail_silently=True,
                )
        except Exception as e:
            print(f"Error sending welcome newsletter email: {e}")


@receiver(post_save, sender=ContactMessage)
def update_contact_statistics(sender, instance, created, **kwargs):
    """
    Update contact statistics (could be used for analytics)
    """
    if created:
        # In a production app, you might update some statistics here
        # For example, increment a counter or update a dashboard
        pass


