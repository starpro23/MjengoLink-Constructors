from django.db import models
from django.contrib.auth.models import User
from projects.models import Project, ProjectMilestone
from decimal import Decimal
from django.core.validators import MinValueValidator


class Payment(models.Model):
    """Payment transactions"""
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]

    PAYMENT_TYPES = [
        ('milestone', 'Milestone Payment'),
        ('deposit', 'Deposit'),
        ('final', 'Final Payment'),
        ('refund', 'Refund'),
        ('service_fee', 'Service Fee'),
        ('other', 'Other'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    milestone = models.ForeignKey(ProjectMilestone, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='payment')

    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # M-Pesa specific fields
    mpesa_code = models.CharField(max_length=50, blank=True)
    mpesa_number = models.CharField(max_length=20, blank=True)
    mpesa_receipt = models.CharField(max_length=100, blank=True)

    # Bank transfer fields
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)

    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # For failed payments
    failure_reason = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        """Calculate net amount before saving"""
        if not self.transaction_id:
            # Generate unique transaction ID
            import uuid
            self.transaction_id = f"MJL-{uuid.uuid4().hex[:12].upper()}"

        # Calculate net amount (amount - service fee)
        self.net_amount = self.amount - self.service_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.transaction_id} - KES {self.amount:,}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payer', 'status']),
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['project', 'status']),
        ]


class Invoice(models.Model):
    """Invoices for payments"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices_received')
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices_sent')

    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    description = models.TextField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Payment link for online payment
    payment_link = models.URLField(blank=True)
    payment_link_expiry = models.DateTimeField(null=True, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Generate invoice number and calculate totals"""
        if not self.invoice_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            # In production, use a sequence or random string
            import uuid
            random_str = uuid.uuid4().hex[:6].upper()
            self.invoice_number = f"INV-{date_str}-{random_str}"

        # Calculate total amount
        self.total_amount = self.amount + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} - KES {self.total_amount:,}"

    class Meta:
        ordering = ['-created_at']


class PaymentDispute(models.Model):
    """Disputes related to payments"""
    SEVERITY_CHOICES = [
        ('low', 'Low - Minor Issue'),
        ('medium', 'Medium - Needs Attention'),
        ('high', 'High - Urgent'),
        ('critical', 'Critical - Immediate Action'),
    ]

    RESOLUTION_CHOICES = [
        ('pending', 'Pending Resolution'),
        ('refund_full', 'Full Refund to Client'),
        ('refund_partial', 'Partial Refund'),
        ('payment_released', 'Payment Released to Artisan'),
        ('project_restart', 'Project Restarted with Different Artisan'),
        ('mediation', 'Mediation Required'),
        ('escalated', 'Escalated to Authorities'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    dispute_id = models.CharField(max_length=50, unique=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='disputes')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disputes_raised')
    raised_against = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disputes_against')

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('payment', 'Payment Issue'),
        ('quality', 'Quality of Work'),
        ('timeline', 'Timeline Delay'),
        ('communication', 'Communication Issue'),
        ('behavior', 'Unprofessional Behavior'),
        ('safety', 'Safety Concern'),
        ('other', 'Other'),
    ])
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('awaiting_response', 'Awaiting Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], default='open')

    # Resolution details
    resolution = models.CharField(max_length=30, choices=RESOLUTION_CHOICES, blank=True)
    resolution_details = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_disputes')
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Evidence
    evidence_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Generate dispute ID"""
        if not self.dispute_id:
            import uuid
            self.dispute_id = f"DSP-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dispute {self.dispute_id} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class DisputeEvidence(models.Model):
    """Evidence files for disputes"""
    dispute = models.ForeignKey(PaymentDispute, on_delete=models.CASCADE, related_name='evidence')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    evidence_type = models.CharField(max_length=50, choices=[
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('chat_log', 'Chat Log'),
        ('other', 'Other'),
    ])
    file = models.FileField(upload_to='dispute_evidence/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence for {self.dispute.dispute_id}"

    class Meta:
        ordering = ['-uploaded_at']


class Wallet(models.Model):
    """User wallet for holding funds"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hold_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                       help_text="Amount held for pending transactions")
    total_deposited = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_balance(self):
        return self.balance - self.hold_balance

    def __str__(self):
        return f"Wallet: {self.user.username} - KES {self.balance:,}"

    class Meta:
        ordering = ['-updated_at']


class Transaction(models.Model):
    """Wallet transactions"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('fee', 'Fee'),
        ('hold', 'Hold'),
        ('release', 'Release'),
        ('transfer', 'Transfer'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2)
    new_balance = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Generate transaction ID"""
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"WLT-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_transaction_type_display()}: KES {self.amount:,}"

    class Meta:
        ordering = ['-created_at']


