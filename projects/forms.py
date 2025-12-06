"""
Forms for Projects App
Contains all forms for project management, bidding, messaging, etc.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import Project, ProjectImage, Bid, ProjectMessage, ProjectMilestone, ProjectReview
from django.forms import inlineformset_factory

class ProjectForm(forms.ModelForm):
    """Form for creating and updating projects"""

    # images = forms.FileField(
    #     required=False,
    #     widget=forms.FileInput(attrs={'multiple': True}),
    #     help_text="Upload up to 5 images (optional)"
    # )

    class Meta:
        model = Project
        fields = [
            'title', 'category', 'description', 'location',
            'budget_min', 'budget_max', 'urgency', 'preferred_timeline',
            'special_requirements', 'bidding_deadline',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'special_requirements': forms.Textarea(attrs={'rows': 3}),
            'bidding_deadline': forms.DateInput(attrs={'type': 'date'}),
            'preferred_timeline': forms.TextInput(attrs={'placeholder': 'e.g., 2 weeks, 1 month'}),
        }
        labels = {
            'budget_min': 'Minimum Budget (KES)',
            'budget_max': 'Maximum Budget (KES)',
        }
# 
#     ProjectImageFormSet = inlineformset_factory(
#         Project,
#         ProjectImage,
#         fields=['image', 'caption'],
#         extra=5,
#         max_num=5,
#         can_delete=True
#     )

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')
        bidding_deadline = cleaned_data.get('bidding_deadline')

        # Validate budget range
        if budget_min and budget_max:
            if budget_min < 0 or budget_max < 0:
                raise ValidationError("Budget cannot be negative.")
            if budget_min > budget_max:
                raise ValidationError("Minimum budget cannot be greater than maximum budget.")
            if budget_max > 100000000:  # 100 million KES limit
                raise ValidationError("Maximum budget cannot exceed KES 100,000,000.")

        # Validate bidding deadline
        if bidding_deadline:
            if bidding_deadline < timezone.now().date():
                raise ValidationError("Bidding deadline cannot be in the past.")
            if bidding_deadline > timezone.now().date() + timezone.timedelta(days=90):
                raise ValidationError("Bidding deadline cannot be more than 90 days from now.")

        return cleaned_data


class ProjectImageForm(forms.ModelForm):
    """Form for project images"""

    class Meta:
        model = ProjectImage
        fields = ['image', 'is_primary']


class BidForm(forms.ModelForm):
    """Form for placing bids"""

    class Meta:
        model = Bid
        fields = ['amount', 'proposal', 'timeline']
        widgets = {
            'proposal': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe your approach, materials you\'ll use, timeline, and why you\'re the best fit...'
            }),
            'timeline': forms.TextInput(attrs={
                'placeholder': 'e.g., 2 weeks, 1 month'
            }),
        }
        labels = {
            'amount': 'Bid Amount (KES)',
            'proposal': 'Your Proposal',
            'timeline': 'Timeline',
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Bid amount must be greater than 0.")
        if amount and amount > 100000000:  # 100 million KES limit
            raise ValidationError("Bid amount cannot exceed KES 100,000,000.")
        return amount


class MessageForm(forms.ModelForm):
    """Form for sending messages"""

    class Meta:
        model = ProjectMessage
        fields = ["message"]

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if not message or len(message.strip()) < 1:
            raise forms.ValidationError("Message cannot be empty.")
        if len(message) > 10000:
            raise forms.ValidationError("Message is too long (maximum 10,000 characters).")
        return message
        # return message


class MilestoneForm(forms.ModelForm):
    """Form for creating/updating milestones"""

    class Meta:
        model = ProjectMilestone
        fields = ['title', 'description', 'due_date', 'amount']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'amount': 'Milestone Payment (KES)',
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 0:
            raise ValidationError("Milestone amount cannot be negative.")
        return amount

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise ValidationError("Due date cannot be in the past.")
        return due_date


class ReviewForm(forms.ModelForm):
    """Form for submitting reviews"""

    class Meta:
        model = ProjectReview
        fields = ['rating', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('content')
        if comment and len(comment.strip()) < 10:
            raise ValidationError("Please provide a more detailed review (at least 10 characters).")
        return comment


class ProjectSearchForm(forms.Form):
    """Form for searching projects"""

    category = forms.ChoiceField(
        required=False,
        choices=[('all', 'All Categories')] + list(Project.CATEGORY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City or Area'
        })
    )
    min_budget = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Budget'
        })
    )
    max_budget = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Budget'
        })
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('budget_low', 'Budget (Low to High)'),
            ('budget_high', 'Budget (High to Low)'),
            ('deadline', 'Deadline (Soonest)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )