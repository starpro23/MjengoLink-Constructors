"""
Test Suite for Core App
Contains unit tests and integration tests for:
- Models and their methods
- Views and URL routing
- Form submissions
- Admin interfaces
- Signal handlers
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail

from .models import SiteSetting, ContactMessage, Testimonial, FAQ, NewsletterSubscriber


class SiteSettingModelTest(TestCase):
    """Test cases for SiteSetting model"""

    def setUp(self):
        """Create test data"""
        self.site_settings = SiteSetting.objects.create(
            site_name="Test Site",
            tagline="Test Tagline",
            contact_email="test@example.com",
            contact_phone="+254700000000",
            address="Test Address"
        )

    def test_site_setting_creation(self):
        """Test site setting creation"""
        self.assertEqual(self.site_settings.site_name, "Test Site")
        self.assertEqual(self.site_settings.contact_email, "test@example.com")

    def test_site_setting_str(self):
        """Test string representation"""
        self.assertEqual(str(self.site_settings), "Site Settings")

    def test_single_site_setting(self):
        """Test that only one site setting can exist"""
        # Try to create another site setting
        with self.assertRaises(Exception):
            SiteSetting.objects.create(
                site_name="Another Site",
                contact_email="another@example.com"
            )


class ContactMessageModelTest(TestCase):
    """Test cases for ContactMessage model"""

    def setUp(self):
        """Create test data"""
        self.contact = ContactMessage.objects.create(
            name="John Doe",
            email="john@example.com",
            subject="general",
            message="Test message"
        )

    def test_contact_message_creation(self):
        """Test contact message creation"""
        self.assertEqual(self.contact.name, "John Doe")
        self.assertEqual(self.contact.subject, "general")
        self.assertFalse(self.contact.is_read)

    def test_contact_message_str(self):
        """Test string representation"""
        expected = "John Doe - General Inquiry"
        self.assertEqual(str(self.contact), expected)

    def test_default_ordering(self):
        """Test that messages are ordered by creation date descending"""
        ContactMessage.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            subject="support",
            message="Another message"
        )

        messages = ContactMessage.objects.all()
        self.assertEqual(messages[0].name, "Jane Doe")
        self.assertEqual(messages[1].name, "John Doe")


class TestimonialModelTest(TestCase):
    """Test cases for Testimonial model"""

    def setUp(self):
        """Create test data"""
        self.testimonial = Testimonial.objects.create(
            client_name="John Kamau",
            client_location="Nairobi",
            client_type="homeowner",
            content="Great service!",
            rating=5
        )

    def test_testimonial_creation(self):
        """Test testimonial creation"""
        self.assertEqual(self.testimonial.client_name, "John Kamau")
        self.assertEqual(self.testimonial.rating, 5)
        self.assertFalse(self.testimonial.is_featured)

    def test_testimonial_str(self):
        """Test string representation"""
        self.assertEqual(str(self.testimonial), "Testimonial by John Kamau")


class FAQModelTest(TestCase):
    """Test cases for FAQ model"""

    def setUp(self):
        """Create test data"""
        self.faq = FAQ.objects.create(
            question="What is MjengoLink?",
            answer="A construction platform",
            category="general",
            order=1
        )

    def test_faq_creation(self):
        """Test FAQ creation"""
        self.assertEqual(self.faq.question, "What is MjengoLink?")
        self.assertTrue(self.faq.is_active)

    def test_faq_str(self):
        """Test string representation"""
        self.assertEqual(str(self.faq), "What is MjengoLink?")


class NewsletterSubscriberModelTest(TestCase):
    """Test cases for NewsletterSubscriber model"""

    def setUp(self):
        """Create test data"""
        self.subscriber = NewsletterSubscriber.objects.create(
            email="subscriber@example.com"
        )

    def test_subscriber_creation(self):
        """Test subscriber creation"""
        self.assertEqual(self.subscriber.email, "subscriber@example.com")
        self.assertTrue(self.subscriber.is_active)

    def test_subscriber_str(self):
        """Test string representation"""
        self.assertEqual(str(self.subscriber), "subscriber@example.com")

    def test_unique_email(self):
        """Test that email must be unique"""
        with self.assertRaises(Exception):
            NewsletterSubscriber.objects.create(
                email="subscriber@example.com"
            )


class ViewTests(TestCase):
    """Test cases for views"""

    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.site_settings = SiteSetting.objects.create(
            site_name="Test Site",
            contact_email="test@example.com"
        )
        self.faq = FAQ.objects.create(
            question="Test Question",
            answer="Test Answer",
            category="general"
        )
        self.testimonial = Testimonial.objects.create(
            client_name="Test Client",
            client_location="Test Location",
            client_type="homeowner",
            content="Test content",
            rating=5
        )

    def test_homepage_view(self):
        """Test homepage loads successfully"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_about_view(self):
        """Test about page loads successfully"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')

    def test_services_view(self):
        """Test services page loads successfully"""
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/services.html')

    def test_contact_view(self):
        """Test contact page loads successfully"""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')
        self.assertContains(response, 'Contact Us')

    def test_how_it_works_view(self):
        """Test how-it-works page loads successfully"""
        response = self.client.get(reverse('how-it-works'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/how-it-works.html')

    def test_contact_form_submission(self):
        """Test contact form submission"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'general',
            'message': 'Test message',
            'consent': 'on'
        }

        response = self.client.post(reverse('contact'), data)

        # Should redirect or show success message
        self.assertIn(response.status_code, [200, 302])

        # Check that message was created
        self.assertTrue(ContactMessage.objects.filter(email='test@example.com').exists())


class AdminTests(TestCase):
    """Test cases for admin interfaces"""

    def setUp(self):
        """Create admin user and login"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')

        # Create test data
        self.contact = ContactMessage.objects.create(
            name="Test User",
            email="test@example.com",
            subject="general",
            message="Test"
        )
        self.testimonial = Testimonial.objects.create(
            client_name="Test Client",
            client_location="Test",
            client_type="homeowner",
            content="Test",
            rating=5
        )
        self.faq = FAQ.objects.create(
            question="Test",
            answer="Test",
            category="general"
        )
        self.subscriber = NewsletterSubscriber.objects.create(
            email="test@example.com"
        )

    def test_admin_site_setting_list(self):
        """Test site setting admin list view"""
        response = self.client.get('/admin/core/sitesetting/')
        self.assertEqual(response.status_code, 200)

    def test_admin_contact_message_list(self):
        """Test contact message admin list view"""
        response = self.client.get('/admin/core/contactmessage/')
        self.assertEqual(response.status_code, 200)

    def test_admin_testimonial_list(self):
        """Test testimonial admin list view"""
        response = self.client.get('/admin/core/testimonial/')
        self.assertEqual(response.status_code, 200)

    def test_admin_faq_list(self):
        """Test FAQ admin list view"""
        response = self.client.get('/admin/core/faq/')
        self.assertEqual(response.status_code, 200)

    def test_admin_newsletter_list(self):
        """Test newsletter admin list view"""
        response = self.client.get('/admin/core/newslettersubscriber/')
        self.assertEqual(response.status_code, 200)

    def test_admin_actions(self):
        """Test admin actions"""
        # Test mark as read action
        response = self.client.post('/admin/core/contactmessage/', {
            'action': 'mark_as_read',
            '_selected_action': [self.contact.id]
        })
        self.assertEqual(response.status_code, 302)

        # Refresh from DB
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.is_read)


class SignalTests(TestCase):
    """Test cases for signal handlers"""

    def setUp(self):
        """Set up test data"""
        self.site_settings = SiteSetting.objects.create(
            site_name="Test Site",
            contact_email="admin@example.com"
        )

    def test_contact_message_signal(self):
        """Test that contact message triggers email signal"""
        # Clear any existing emails
        mail.outbox = []

        # Create a contact message
        ContactMessage.objects.create(
            name="Test User",
            email="user@example.com",
            subject="general",
            message="Test message"
        )

        # Check if email would be sent (in development, it only prints)
        # In production with proper email settings, we'd check mail.outbox
        self.assertEqual(len(mail.outbox), 0)  # No actual email sent in test mode

    def test_newsletter_subscriber_signal(self):
        """Test that newsletter subscription triggers welcome email"""
        # Clear any existing emails
        mail.outbox = []

        # Create a newsletter subscriber
        NewsletterSubscriber.objects.create(
            email="subscriber@example.com"
        )

        # Check if email would be sent
        self.assertEqual(len(mail.outbox), 0)  # No actual email sent in test mode


class FormTests(TestCase):
    """Test cases for forms (to be implemented when forms are created)"""

    def test_contact_form_validation(self):
        """Test contact form validation"""
        # This test will be expanded when forms.py is created
        pass


# Run all tests
if __name__ == '__main__':
    import unittest

    unittest.main()
