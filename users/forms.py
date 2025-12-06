"""
User Forms for MVP
Essential forms for user registration and profile management
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

from .models import UserProfile, ArtisanProfile

class UserRegistrationForm(UserCreationForm):
    """
    User registration form for MVP
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Your email address'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number'})
    )
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,  # Uses model directly
        widget=forms.RadioSelect,
        initial='homeowner'
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'user_type', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Update profile
            profile = user.profile
            profile.phone = self.cleaned_data['phone']
            profile.user_type = self.cleaned_data['user_type']
            profile.save()

            # Create artisan profile if needed
            if self.cleaned_data['user_type'] == 'artisan':
                ArtisanProfile.objects.create(user=user)

        return user

class UserProfileForm(forms.ModelForm):
    """
    User profile update form for MVP
    """
    class Meta:
        model = UserProfile
        fields = ['phone', 'location', 'bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

class ArtisanProfileForm(forms.ModelForm):
    """
    Artisan profile form for MVP
    """
    class Meta:
        model = ArtisanProfile
        fields = ['trade', 'experience_years', 'skills']
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 2}),
        }

class LoginForm(forms.Form):
    """
    Simple login form for MVP
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))