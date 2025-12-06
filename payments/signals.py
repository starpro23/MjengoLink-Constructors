"""
Signal Handlers for Payments App
Contains signal receivers for:
- Automatic wallet creation for new users
- Payment status change notifications
- Dispute escalation notifications
- Invoice due date reminders
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Payment, Invoice, PaymentDispute, Wallet
from core.models import SiteSetting


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Create wallet when new user is created
    """
    if created:
        Wallet.objects.create(user=instance)


@receiver(pre_save, sender=Payment)
def handle_payment_status_change(sender, instance, **kwargs):
    """
    Handle payment status changes and send notifications
    """
    if instance.pk:
        try:
            old_instance = Payment.objects.get(pk=instance.pk)

            # Check if status changed
            if old_instance.status != instance.status:
                # Send email notification
                send_payment_status_notification(instance, old_instance.status)

                # Update related project milestones if payment completed
                if instance.status == 'completed' and instance.milestone:
                    instance.milestone.status = 'paid'
                    instance.milestone.save()

        except Payment.DoesNotExist:
            pass


@receiver(post_save, sender=Invoice)
def handle_invoice_creation(sender, instance, created, **kwargs):
    """
    Handle invoice creation and send notification
    """
    if created:
        send_invoice_notification(instance)


@receiver(post_save, sender=PaymentDispute)
def handle_dispute_creation(sender, instance, created, **kwargs):
    """
    Handle dispute creation and send notifications
    """
    if created:
        send_dispute_notification(instance)

    # Check if dispute was resolved
    if instance.pk and instance.resolved_at:
        try:
            old_instance = PaymentDispute.objects.get(pk=instance.pk)
            if not old_instance.resolved_at and instance.resolved_at:
                send_dispute_resolution_notification(instance)
        except PaymentDispute.DoesNotExist:
            pass


def send_payment_status_notification(payment, old_status):
    """
    Send email notification for payment status change
    """
    try:
        site_settings = SiteSetting.objects.first()
        if not site_settings:
            return

        # Determine recipients
        recipients = [payment.payer.email, payment.recipient.email]

        # Prepare email content
        subject = f"Payment Status Update: {payment.get_status_display()}"

        html_message = render_to_string('emails/payment_status_update.html', {
            'payment': payment,
            'old_status': old_status,
            'site_name': site_settings.site_name,
            'contact_email': site_settings.contact_email,
        })

        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=site_settings.contact_email,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=True,
        )

    except Exception as e:
        if settings.DEBUG:
            print(f"Error sending payment status notification: {e}")


def send_invoice_notification(invoice):
    """
    Send email notification for new invoice
    """
    try:
        site_settings = SiteSetting.objects.first()
        if not site_settings:
            return

        subject = f"New Invoice: {invoice.invoice_number}"

        html_message = render_to_string('emails/new_invoice.html', {
            'invoice': invoice,
            'site_name': site_settings.site_name,
            'payment_link': '#',  # Would be actual payment link in production
        })

        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=site_settings.contact_email,
            recipient_list=[invoice.client.email],
            html_message=html_message,
            fail_silently=True,
        )

    except Exception as e:
        if settings.DEBUG:
            print(f"Error sending invoice notification: {e}")


def send_dispute_notification(dispute):
    """
    Send email notification for new dispute
    """
    try:
        site_settings = SiteSetting.objects.first()
        if not site_settings:
            return

        subject = f"New Dispute Filed: {dispute.title}"

        # Send to both parties
        for user in [dispute.raised_by, dispute.raised_against]:
            html_message = render_to_string('emails/new_dispute.html', {
                'dispute': dispute,
                'user': user,
                'site_name': site_settings.site_name,
            })

            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=site_settings.contact_email,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )

        # Also notify admin
        html_message = render_to_string('emails/new_dispute_admin.html', {
            'dispute': dispute,
            'site_name': site_settings.site_name,
        })

        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"[ADMIN] New Dispute: {dispute.dispute_id}",
            message=plain_message,
            from_email=site_settings.contact_email,
            recipient_list=[site_settings.contact_email],
            html_message=html_message,
            fail_silently=True,
        )

    except Exception as e:
        if settings.DEBUG:
            print(f"Error sending dispute notification: {e}")


def send_dispute_resolution_notification(dispute):
    """
    Send email notification for dispute resolution
    """
    try:
        site_settings = SiteSetting.objects.first()
        if not site_settings:
            return

        subject = f"Dispute Resolved: {dispute.title}"

        # Send to both parties
        for user in [dispute.raised_by, dispute.raised_against]:
            html_message = render_to_string('emails/dispute_resolved.html', {
                'dispute': dispute,
                'user': user,
                'site_name': site_settings.site_name,
            })

            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=site_settings.contact_email,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )

    except Exception as e:
        if settings.DEBUG:
            print(f"Error sending dispute resolution notification: {e}")


# Schedule daily invoice due date reminders
def check_due_invoices():
    """
    Check for invoices due today or overdue and send reminders
    This would be scheduled as a cron job or Celery task
    """
    today = timezone.now().date()

    # Find invoices due today or overdue
    invoices = Invoice.objects.filter(
        status__in=['sent', 'viewed'],
        due_date__lte=today
    )

    for invoice in invoices:
        try:
            site_settings = SiteSetting.objects.first()
            if not site_settings:
                continue

            # Determine if overdue
            is_overdue = invoice.due_date < today

            subject = "Invoice Reminder" if not is_overdue else "Invoice Overdue"

            html_message = render_to_string('emails/invoice_reminder.html', {
                'invoice': invoice,
                'is_overdue': is_overdue,
                'days_overdue': (today - invoice.due_date).days if is_overdue else 0,
                'site_name': site_settings.site_name,
                'payment_link': '#',
            })

            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=site_settings.contact_email,
                recipient_list=[invoice.client.email],
                html_message=html_message,
                fail_silently=True,
            )

            # Update status if overdue
            if is_overdue and invoice.status != 'overdue':
                invoice.status = 'overdue'
                invoice.save()

        except Exception as e:
            if settings.DEBUG:
                print(f"Error sending invoice reminder: {e}")


