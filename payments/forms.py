"""
Form Definitions for Payments App
Contains Django forms for:
- Payment creation and processing
- Invoice generation
- Dispute submission
- Evidence upload
- Wallet operations
"""

from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Payment, Invoice, PaymentDispute, DisputeEvidence, Wallet
from projects.models import Project, ProjectMilestone
from users.models import UserProfile


class PaymentForm(forms.ModelForm):
    """Form for creating payments"""

    class Meta:
        model = Payment
        fields = ['recipient', 'project', 'milestone', 'amount',
                  'payment_method', 'payment_type', 'description']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'milestone': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this payment...'
            }),
        }
        labels = {
            'recipient': 'Pay To',
            'amount': 'Amount (KES)',
            'payment_method': 'Payment Method',
            'payment_type': 'Payment Type',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter recipients to users who are not the payer
        if self.user:
            self.fields['recipient'].queryset = self.fields['recipient'].queryset.exclude(id=self.user.id)

            # Filter projects to those belonging to the user
            self.fields['project'].queryset = Project.objects.filter(
                homeowner=self.user
            ).filter(status__in=['assigned', 'in_progress'])

            # Filter milestones based on selected project
            if 'project' in self.data:
                try:
                    project_id = int(self.data.get('project'))
                    self.fields['milestone'].queryset = ProjectMilestone.objects.filter(
                        project_id=project_id
                    )
                except (ValueError, TypeError):
                    pass
            elif self.instance.pk and self.instance.project:
                self.fields['milestone'].queryset = self.instance.project.milestones.all()
            else:
                self.fields['milestone'].queryset = ProjectMilestone.objects.none()

    def clean_amount(self):
        """Validate amount"""
        amount = self.cleaned_data.get('amount')

        if amount is None or amount <= 0:
            raise ValidationError('Amount must be greater than 0')

        if amount > 1000000:  # 1 million KES limit
            raise ValidationError('Amount cannot exceed KES 1,000,000')

        return amount

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()

        project = cleaned_data.get('project')
        milestone = cleaned_data.get('milestone')
        recipient = cleaned_data.get('recipient')

        # Validate milestone belongs to project
        if milestone and project:
            if milestone.project != project:
                raise ValidationError({
                    'milestone': 'Selected milestone does not belong to the selected project.'
                })

        # Validate recipient is assigned to project
        if project and recipient:
            if project.assigned_to and project.assigned_to != recipient:
                raise ValidationError({
                    'recipient': f'Selected recipient is not assigned to this project. '
                                 f'Project is assigned to {project.assigned_to.get_full_name()}.'
                })

        return cleaned_data


class InvoiceForm(forms.ModelForm):
    """Form for creating invoices"""

    class Meta:
        model = Invoice
        fields = ['client', 'artisan', 'project', 'amount',
                  'tax_amount', 'description', 'due_date']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'artisan': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the services or items included in this invoice...'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class DisputeForm(forms.ModelForm):
    """Form for submitting payment disputes"""

    class Meta:
        model = PaymentDispute
        fields = ['payment', 'project', 'raised_against', 'title',
                  'category', 'severity', 'description']
        widgets = {
            'payment': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'raised_against': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of the dispute'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the issue in detail. Include relevant dates, amounts, and communication.'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # Filter payments to those involving the user
            self.fields['payment'].queryset = Payment.objects.filter(
                Q(payer=self.user) | Q(recipient=self.user)
            )

            # Filter projects to those involving the user
            self.fields['project'].queryset = Project.objects.filter(
                Q(homeowner=self.user) | Q(assigned_to=self.user)
            )

            # Filter raised_against to exclude self
            self.fields['raised_against'].queryset = self.fields['raised_against'].queryset.exclude(id=self.user.id)

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()

        payment = cleaned_data.get('payment')
        raised_against = cleaned_data.get('raised_against')

        # Validate raised_against is related to the payment
        if payment and raised_against:
            if raised_against not in [payment.payer, payment.recipient]:
                raise ValidationError({
                    'raised_against': 'Selected user must be either the payer or recipient of the payment.'
                })

            if raised_against == self.user:
                raise ValidationError({
                    'raised_against': 'You cannot raise a dispute against yourself.'
                })

        return cleaned_data


class EvidenceForm(forms.ModelForm):
    """Form for uploading dispute evidence"""

    class Meta:
        model = DisputeEvidence
        fields = ['evidence_type', 'file', 'description']
        widgets = {
            'evidence_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what this evidence shows...'
            }),
        }

    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')

        if file:
            # Check file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise ValidationError('File size cannot exceed 10MB.')

            # Check file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif',
                'application/pdf',
                'application/msword',  # .doc
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
                'text/plain',
            ]

            if file.content_type not in allowed_types:
                raise ValidationError(
                    'File type not allowed. Allowed types: Images, PDF, Word documents, text files.'
                )

        return file


class WalletWithdrawalForm(forms.Form):
    """Form for wallet withdrawals"""

    METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
    ]

    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100.00'))],  # Minimum 100 KES
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '100',
            'placeholder': 'Minimum KES 100.00'
        }),
        label='Amount to Withdraw (KES)'
    )

    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Withdrawal Method'
    )

    account_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'For bank transfer: Bank name, account number, account name\n'
                           'For M-Pesa: Phone number (if different from profile)'
        }),
        label='Account Details'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        """Validate withdrawal amount"""
        amount = self.cleaned_data.get('amount')

        if amount is None or amount <= 0:
            raise ValidationError('Amount must be greater than 0')

        # Check if user has sufficient balance
        if self.user:
            try:
                wallet = Wallet.objects.get(user=self.user)
                if amount > wallet.available_balance:
                    raise ValidationError(
                        f'Insufficient funds. Available balance: KES {wallet.available_balance:,.2f}'
                    )
            except Wallet.DoesNotExist:
                raise ValidationError('Wallet not found')

        # Maximum withdrawal limit
        if amount > 50000:  # 50,000 KES limit per withdrawal
            raise ValidationError('Maximum withdrawal amount is KES 50,000')

        return amount

    def clean_account_details(self):
        """Validate account details based on method"""
        method = self.cleaned_data.get('method')
        details = self.cleaned_data.get('account_details', '').strip()

        if method == 'bank' and not details:
            raise ValidationError(
                'Please provide bank details for bank transfer withdrawals.'
            )

        return details


