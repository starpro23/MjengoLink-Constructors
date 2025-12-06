"""
Form Definitions for Core App
Contains Django forms for:
- Contact form submission
- Newsletter subscription
- Feedback and inquiries
- Site search
"""

from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import ContactMessage, NewsletterSubscriber


class ContactForm(forms.ModelForm):
    """Contact form for website inquiries"""

    consent = forms.BooleanField(
        required=True,
        label='I agree to receive responses via email or phone.',
        error_messages={'required': 'You must agree to the terms.'}
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your phone number (optional)'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message...',
                'rows': 5
            }),
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'subject': 'Subject',
            'message': 'Message',
        }
        error_messages = {
            'name': {'required': 'Please enter your name.'},
            'email': {'required': 'Please enter your email address.'},
            'message': {'required': 'Please enter your message.'},
            'subject': {'required': 'Please select a subject.'},
        }

    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError('Please enter a valid email address.')
        return email

    def clean_phone(self):
        """Basic phone number validation"""
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not phone.replace(' ', '').replace('+', '').replace('-', '').isdigit():
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_message(self):
        """Validate message length"""
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Please provide a more detailed message (at least 10 characters).')
        if len(message) > 2000:
            raise forms.ValidationError('Message is too long (maximum 2000 characters).')
        return message


class NewsletterForm(forms.ModelForm):
    """Newsletter subscription form"""

    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            })
        }
        labels = {
            'email': 'Email Address'
        }

    def clean_email(self):
        """Validate email and check if already subscribed"""
        email = self.cleaned_data.get('email')

        # Basic email validation
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError('Please enter a valid email address.')

        # Check if already subscribed and active
        existing = NewsletterSubscriber.objects.filter(email=email, is_active=True).exists()
        if existing:
            raise forms.ValidationError('This email is already subscribed to our newsletter.')

        return email


class FeedbackForm(forms.Form):
    """General feedback form (not tied to a model)"""

    FEEDBACK_TYPES = [
        ('suggestion', 'Suggestion'),
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('complaint', 'Complaint'),
        ('praise', 'Praise'),
        ('other', 'Other'),
    ]

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name (optional)'
        }),
        required=False
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email (optional)'
        }),
        required=False
    )

    feedback_type = forms.ChoiceField(
        choices=FEEDBACK_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='suggestion'
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your feedback...',
            'rows': 4
        }),
        min_length=10,
        max_length=1000
    )

    def clean_email(self):
        """Validate email if provided"""
        email = self.cleaned_data.get('email')
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError('Please enter a valid email address.')
        return email

    def clean_message(self):
        """Validate feedback message"""
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Please provide more details (at least 10 characters).')
        return message


class SearchForm(forms.Form):
    """Site search form"""

    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for projects, artisans, or help...'
        }),
        required=True
    )

    SEARCH_CATEGORIES = [
        ('all', 'Everything'),
        ('projects', 'Projects'),
        ('artisans', 'Artisans'),
        ('help', 'Help Articles'),
    ]

    category = forms.ChoiceField(
        choices=SEARCH_CATEGORIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='all',
        required=False
    )

    def clean_query(self):
        """Validate search query"""
        query = self.cleaned_data.get('query', '').strip()
        if len(query) < 2:
            raise forms.ValidationError('Search query must be at least 2 characters long.')
        return query


