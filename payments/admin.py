"""
Django Admin Configuration for Payments App
Contains admin interfaces for:
- Payment transactions monitoring
- Invoice management
- Dispute resolution
- Wallet administration
- M-Pesa transaction logs
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Payment, Invoice, PaymentDispute, DisputeEvidence, Wallet, Transaction


class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment transactions"""
    list_display = ('transaction_id', 'payer_info', 'recipient_info', 'amount_formatted',
                    'payment_method', 'status_badge', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_type', 'created_at')
    search_fields = ('transaction_id', 'payer__username', 'recipient__username',
                     'mpesa_code', 'mpesa_receipt')
    readonly_fields = ('transaction_id', 'created_at', 'processed_at', 'completed_at',
                       'payer_info', 'recipient_info', 'project_link')
    list_per_page = 50

    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'payment_method', 'payment_type', 'status')
        }),
        ('Parties', {
            'fields': ('payer_info', 'recipient_info', 'project_link')
        }),
        ('Amount Details', {
            'fields': ('amount', 'service_fee', 'net_amount')
        }),
        ('M-Pesa Details', {
            'fields': ('mpesa_code', 'mpesa_number', 'mpesa_receipt'),
            'classes': ('collapse',)
        }),
        ('Bank Transfer Details', {
            'fields': ('bank_name', 'account_number', 'transaction_reference'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('description', 'notes', 'failure_reason')
        }),
    )

    def payer_info(self, obj):
        """Display payer information"""
        if obj.payer:
            url = reverse('admin:auth_user_change', args=[obj.payer.id])
            return format_html('<a href="{}">{}</a>', url, obj.payer.get_full_name())
        return '-'

    payer_info.short_description = 'Payer'

    def recipient_info(self, obj):
        """Display recipient information"""
        if obj.recipient:
            url = reverse('admin:auth_user_change', args=[obj.recipient.id])
            return format_html('<a href="{}">{}</a>', url, obj.recipient.get_full_name())
        return '-'

    recipient_info.short_description = 'Recipient'

    def project_link(self, obj):
        """Display project link if available"""
        if obj.project:
            url = reverse('admin:projects_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.title)
        return '-'

    project_link.short_description = 'Project'

    def amount_formatted(self, obj):
        """Format amount with KES"""
        return f"KES {obj.amount:,.2f}"

    amount_formatted.short_description = 'Amount'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'secondary',
            'refunded': 'primary',
            'disputed': 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    actions = ['mark_as_completed', 'mark_as_failed', 'process_refund']

    def mark_as_completed(self, request, queryset):
        """Mark selected payments as completed"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} payment(s) marked as completed.')

    mark_as_completed.short_description = "Mark as completed"

    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed"""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.')

    mark_as_failed.short_description = "Mark as failed"

    def process_refund(self, request, queryset):
        """Process refund for selected payments"""
        # In production, this would trigger actual refund logic
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} payment(s) marked as refunded.')

    process_refund.short_description = "Process refund"


class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoices"""
    list_display = ('invoice_number', 'client_info', 'artisan_info', 'total_amount_formatted',
                    'status_badge', 'due_date', 'created_at')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('invoice_number', 'client__username', 'artisan__username')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at', 'sent_at', 'paid_at',
                       'client_info', 'artisan_info', 'project_link')

    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'project_link', 'status', 'due_date')
        }),
        ('Parties', {
            'fields': ('client_info', 'artisan_info')
        }),
        ('Amount Details', {
            'fields': ('amount', 'tax_amount', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_link', 'payment_link_expiry'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )

    def client_info(self, obj):
        """Display client information"""
        if obj.client:
            url = reverse('admin:auth_user_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.get_full_name())
        return '-'

    client_info.short_description = 'Client'

    def artisan_info(self, obj):
        """Display artisan information"""
        if obj.artisan:
            url = reverse('admin:auth_user_change', args=[obj.artisan.id])
            return format_html('<a href="{}">{}</a>', url, obj.artisan.get_full_name())
        return '-'

    artisan_info.short_description = 'Artisan'

    def project_link(self, obj):
        """Display project link"""
        if obj.project:
            url = reverse('admin:projects_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.title)
        return '-'

    project_link.short_description = 'Project'

    def total_amount_formatted(self, obj):
        """Format total amount"""
        return f"KES {obj.total_amount:,.2f}"

    total_amount_formatted.short_description = 'Total Amount'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'draft': 'secondary',
            'sent': 'info',
            'viewed': 'primary',
            'paid': 'success',
            'overdue': 'warning',
            'cancelled': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    actions = ['send_invoice', 'mark_as_paid', 'mark_as_overdue']

    def send_invoice(self, request, queryset):
        """Send selected invoices"""
        updated = queryset.update(status='sent')
        self.message_user(request, f'{updated} invoice(s) marked as sent.')

    send_invoice.short_description = "Send invoice"

    def mark_as_paid(self, request, queryset):
        """Mark selected invoices as paid"""
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} invoice(s) marked as paid.')

    mark_as_paid.short_description = "Mark as paid"


class DisputeEvidenceInline(admin.TabularInline):
    """Inline admin for dispute evidence"""
    model = DisputeEvidence
    extra = 0
    readonly_fields = ('uploaded_at',)
    fields = ('evidence_type', 'file', 'description', 'uploaded_at')


class PaymentDisputeAdmin(admin.ModelAdmin):
    """Admin interface for Payment Disputes"""
    list_display = ('dispute_id', 'title', 'raised_by_info', 'raised_against_info',
                    'category', 'severity_badge', 'status_badge', 'created_at')
    list_filter = ('status', 'category', 'severity', 'created_at')
    search_fields = ('dispute_id', 'title', 'raised_by__username', 'raised_against__username')
    readonly_fields = ('dispute_id', 'created_at', 'updated_at', 'resolved_at',
                       'raised_by_info', 'raised_against_info', 'payment_link', 'project_link')
    inlines = [DisputeEvidenceInline]

    fieldsets = (
        ('Dispute Information', {
            'fields': ('dispute_id', 'title', 'category', 'severity', 'status')
        }),
        ('Parties', {
            'fields': ('raised_by_info', 'raised_against_info')
        }),
        ('Related Items', {
            'fields': ('payment_link', 'project_link')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Resolution', {
            'fields': ('resolution', 'resolution_details', 'resolved_by', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Evidence', {
            'fields': ('evidence_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def raised_by_info(self, obj):
        """Display who raised the dispute"""
        if obj.raised_by:
            url = reverse('admin:auth_user_change', args=[obj.raised_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.raised_by.get_full_name())
        return '-'

    raised_by_info.short_description = 'Raised By'

    def raised_against_info(self, obj):
        """Display who the dispute is against"""
        if obj.raised_against:
            url = reverse('admin:auth_user_change', args=[obj.raised_against.id])
            return format_html('<a href="{}">{}</a>', url, obj.raised_against.get_full_name())
        return '-'

    raised_against_info.short_description = 'Raised Against'

    def payment_link(self, obj):
        """Display payment link"""
        if obj.payment:
            url = reverse('admin:payments_payment_change', args=[obj.payment.id])
            return format_html('<a href="{}">View Payment</a>', url)
        return '-'

    payment_link.short_description = 'Payment'

    def project_link(self, obj):
        """Display project link"""
        if obj.project:
            url = reverse('admin:projects_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.title)
        return '-'

    project_link.short_description = 'Project'

    def severity_badge(self, obj):
        """Display severity as colored badge"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        color = colors.get(obj.severity, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_severity_display()
        )

    severity_badge.short_description = 'Severity'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'open': 'danger',
            'under_review': 'warning',
            'awaiting_response': 'info',
            'resolved': 'success',
            'closed': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    actions = ['mark_as_resolved', 'mark_as_closed', 'escalate_dispute']

    def mark_as_resolved(self, request, queryset):
        """Mark selected disputes as resolved"""
        updated = queryset.update(status='resolved', resolved_by=request.user)
        self.message_user(request, f'{updated} dispute(s) marked as resolved.')

    mark_as_resolved.short_description = "Mark as resolved"

    def escalate_dispute(self, request, queryset):
        """Escalate selected disputes"""
        updated = queryset.update(severity='critical')
        self.message_user(request, f'{updated} dispute(s) escalated to critical.')

    escalate_dispute.short_description = "Escalate to critical"


class WalletAdmin(admin.ModelAdmin):
    """Admin interface for Wallets"""
    list_display = ('user_info', 'balance_formatted', 'hold_balance_formatted',
                    'available_balance_formatted', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user_info', 'created_at', 'updated_at')

    fieldsets = (
        ('Wallet Information', {
            'fields': ('user_info', 'is_active')
        }),
        ('Balance Details', {
            'fields': ('balance', 'hold_balance', 'available_balance')
        }),
        ('Transaction Totals', {
            'fields': ('total_deposited', 'total_withdrawn'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_info(self, obj):
        """Display user information"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
        return '-'

    user_info.short_description = 'User'

    def balance_formatted(self, obj):
        """Format balance"""
        return f"KES {obj.balance:,.2f}"

    balance_formatted.short_description = 'Balance'

    def hold_balance_formatted(self, obj):
        """Format hold balance"""
        return f"KES {obj.hold_balance:,.2f}"

    hold_balance_formatted.short_description = 'Hold Balance'

    def available_balance_formatted(self, obj):
        """Format available balance"""
        return f"KES {obj.available_balance:,.2f}"

    available_balance_formatted.short_description = 'Available'

    actions = ['activate_wallets', 'deactivate_wallets']

    def activate_wallets(self, request, queryset):
        """Activate selected wallets"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} wallet(s) activated.')

    activate_wallets.short_description = "Activate wallets"

    def deactivate_wallets(self, request, queryset):
        """Deactivate selected wallets"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} wallet(s) deactivated.')

    deactivate_wallets.short_description = "Deactivate wallets"


class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Wallet Transactions"""
    list_display = ('transaction_id', 'wallet_user', 'transaction_type_badge',
                    'amount_formatted', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'description')
    readonly_fields = ('transaction_id', 'created_at', 'wallet_user')

    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'wallet_user', 'transaction_type')
        }),
        ('Amount Details', {
            'fields': ('amount', 'previous_balance', 'new_balance')
        }),
        ('Reference Information', {
            'fields': ('description', 'reference'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def wallet_user(self, obj):
        """Display wallet user"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
        return '-'

    wallet_user.short_description = 'User'

    def amount_formatted(self, obj):
        """Format amount with sign"""
        sign = '+' if obj.transaction_type in ['deposit', 'refund'] else '-'
        return f"{sign}KES {obj.amount:,.2f}"

    amount_formatted.short_description = 'Amount'

    def transaction_type_badge(self, obj):
        """Display transaction type as badge"""
        colors = {
            'deposit': 'success',
            'withdrawal': 'danger',
            'payment': 'primary',
            'refund': 'info',
            'fee': 'warning',
            'hold': 'secondary',
            'release': 'dark',
            'transfer': 'dark',
        }
        color = colors.get(obj.transaction_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_transaction_type_display()
        )

    transaction_type_badge.short_description = 'Type'


# Register models with admin site
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(PaymentDispute, PaymentDisputeAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
