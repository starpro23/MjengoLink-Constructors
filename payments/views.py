"""
View Functions for Payments App
Contains views for:
- Payment processing and initiation
- Invoice management
- Transaction history
- Dispute handling
- Wallet management
- M-Pesa integration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Q, Sum
from decimal import Decimal

from .models import Payment, Invoice, PaymentDispute, DisputeEvidence, Wallet, Transaction
from projects.models import Project, ProjectMilestone
from .forms import PaymentForm, InvoiceForm, DisputeForm, EvidenceForm, WalletWithdrawalForm
from .mpesa.client import MpesaClient


class PaymentCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new payment
    Handles payment initiation for projects and milestones
    """
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_create.html'

    def get_form_kwargs(self):
        """Pass request user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Process valid payment form"""
        try:
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.payer = self.request.user

                # Set service fee (5% of amount)
                payment.service_fee = payment.amount * Decimal('0.05')
                payment.net_amount = payment.amount - payment.service_fee

                # Generate transaction ID
                import uuid
                payment.transaction_id = f"MJL-{uuid.uuid4().hex[:12].upper()}"

                payment.save()

                # Handle M-Pesa payment
                if payment.payment_method == 'mpesa':
                    mpesa_client = MpesaClient()

                    # Generate reference
                    reference = f"MJL{payment.id:06d}"

                    # Initiate STK Push
                    if self.request.user.profile.phone:
                        result = mpesa_client.stk_push(
                            phone_number=self.request.user.profile.phone,
                            amount=payment.amount,
                            account_reference=reference,
                            transaction_desc=f"Payment for {payment.description[:50]}"
                        )

                        if result.get('success'):
                            payment.mpesa_code = result.get('checkout_request_id', '')
                            payment.status = 'processing'
                            payment.save()

                            messages.success(self.request,
                                             'Payment initiated! Please check your phone to complete the M-Pesa transaction.')
                        else:
                            payment.status = 'failed'
                            payment.failure_reason = result.get('error_message', 'Unknown error')
                            payment.save()

                            messages.error(self.request,
                                           f'Payment failed: {result.get("error_message")}')
                    else:
                        payment.status = 'failed'
                        payment.failure_reason = 'Phone number not provided'
                        payment.save()

                        messages.error(self.request,
                                       'Please add your phone number to your profile to use M-Pesa.')
                else:
                    # For other payment methods, mark as pending
                    payment.status = 'pending'
                    payment.save()

                    messages.success(self.request,
                                     'Payment created successfully! It will be processed manually.')

                return redirect('payments:payment_detail', pk=payment.id)

        except Exception as e:
            messages.error(self.request, f'Error creating payment: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add project context if provided
        project_id = self.request.GET.get('project')
        milestone_id = self.request.GET.get('milestone')

        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                context['project'] = project

                # Pre-fill recipient if project is assigned
                if project.assigned_to:
                    context['initial'] = {
                        'recipient': project.assigned_to,
                        'project': project,
                        'description': f'Payment for project: {project.title}'
                    }
            except Project.DoesNotExist:
                pass

        if milestone_id:
            try:
                milestone = ProjectMilestone.objects.get(id=milestone_id)
                context['milestone'] = milestone

                # Pre-fill form for milestone payment
                context['initial'] = {
                    'recipient': milestone.project.assigned_to,
                    'project': milestone.project,
                    'milestone': milestone,
                    'amount': milestone.amount,
                    'description': f'Payment for milestone: {milestone.title}'
                }
            except ProjectMilestone.DoesNotExist:
                pass

        return context


class PaymentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View payment details
    Accessible only to payer, recipient, or admin
    """
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

    def test_func(self):
        """Check if user can view this payment"""
        payment = self.get_object()
        user = self.request.user

        return (user == payment.payer or
                user == payment.recipient or
                user.is_staff)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add related information
        if self.object.project:
            context['project'] = self.object.project

        if self.object.milestone:
            context['milestone'] = self.object.milestone

        # Check if user can retry payment
        context['can_retry'] = (
                self.object.status in ['failed', 'cancelled'] and
                self.request.user == self.object.payer
        )

        return context


class PaymentListView(LoginRequiredMixin, ListView):
    """
    List user's payments (both sent and received)
    """
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        """Filter payments for current user"""
        user = self.request.user

        # Get filter parameters
        payment_type = self.request.GET.get('type', 'all')
        status = self.request.GET.get('status', 'all')

        # Base queryset
        queryset = Payment.objects.filter(
            Q(payer=user) | Q(recipient=user)
        ).select_related('payer', 'recipient', 'project')

        # Apply filters
        if payment_type != 'all':
            if payment_type == 'sent':
                queryset = queryset.filter(payer=user)
            elif payment_type == 'received':
                queryset = queryset.filter(recipient=user)

        if status != 'all':
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add stats
        user = self.request.user

        total_sent = Payment.objects.filter(
            payer=user, status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        total_received = Payment.objects.filter(
            recipient=user, status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        context['stats'] = {
            'total_sent': total_sent,
            'total_received': total_received,
            'total_transactions': self.get_queryset().count(),
        }

        # Add filter values
        context['current_type'] = self.request.GET.get('type', 'all')
        context['current_status'] = self.request.GET.get('status', 'all')

        return context


class InvoiceDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View invoice details
    """
    model = Invoice
    template_name = 'payments/invoice_detail.html'
    context_object_name = 'invoice'

    def test_func(self):
        """Check if user can view this invoice"""
        invoice = self.get_object()
        user = self.request.user

        return (user == invoice.client or
                user == invoice.artisan or
                user.is_staff)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if user can pay the invoice
        context['can_pay'] = (
                self.object.status in ['sent', 'viewed', 'overdue'] and
                self.request.user == self.object.client
        )

        return context


class DisputeCreateView(LoginRequiredMixin, CreateView):
    """
    Create a payment dispute
    """
    model = PaymentDispute
    form_class = DisputeForm
    template_name = 'payments/dispute_create.html'
    success_url = reverse_lazy('payments:dispute_list')

    def get_form_kwargs(self):
        """Pass request user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        # Pre-fill payment if provided
        payment_id = self.request.GET.get('payment')
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                kwargs['initial'] = {
                    'payment': payment,
                    'project': payment.project,
                    'raised_against': payment.recipient if payment.payer == self.request.user else payment.payer
                }
            except Payment.DoesNotExist:
                pass

        return kwargs

    def form_valid(self, form):
        """Process valid dispute form"""
        dispute = form.save(commit=False)
        dispute.raised_by = self.request.user

        # Generate dispute ID
        import uuid
        dispute.dispute_id = f"DSP-{uuid.uuid4().hex[:10].upper()}"

        dispute.save()

        messages.success(self.request,
                         'Dispute submitted successfully! Our team will review it within 24 hours.')

        return super().form_valid(form)


class DisputeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View dispute details
    """
    model = PaymentDispute
    template_name = 'payments/dispute_detail.html'
    context_object_name = 'dispute'

    def test_func(self):
        """Check if user can view this dispute"""
        dispute = self.get_object()
        user = self.request.user

        return (user == dispute.raised_by or
                user == dispute.raised_against or
                user.is_staff)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add evidence upload form
        context['evidence_form'] = EvidenceForm()

        # Check if user can add evidence
        context['can_add_evidence'] = (
                self.request.user in [self.object.raised_by, self.object.raised_against] and
                self.object.status != 'closed'
        )

        return context


class AddEvidenceView(LoginRequiredMixin, CreateView):
    """
    Add evidence to a dispute
    """
    model = DisputeEvidence
    form_class = EvidenceForm
    template_name = 'payments/add_evidence.html'

    def dispatch(self, request, *args, **kwargs):
        """Get dispute from URL"""
        self.dispute = get_object_or_404(PaymentDispute, id=kwargs['dispute_id'])

        # Check permissions
        if request.user not in [self.dispute.raised_by, self.dispute.raised_against]:
            messages.error(request, 'You are not authorized to add evidence to this dispute.')
            return redirect('payments:dispute_detail', pk=self.dispute.id)

        if self.dispute.status == 'closed':
            messages.error(request, 'Cannot add evidence to a closed dispute.')
            return redirect('payments:dispute_detail', pk=self.dispute.id)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Process valid evidence form"""
        evidence = form.save(commit=False)
        evidence.dispute = self.dispute
        evidence.uploaded_by = self.request.user
        evidence.save()

        messages.success(self.request,
                         'Evidence added successfully!')

        return redirect('payments:dispute_detail', pk=self.dispute.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dispute'] = self.dispute
        return context


class WalletView(LoginRequiredMixin, DetailView):
    """
    View and manage user wallet
    """
    model = Wallet
    template_name = 'payments/wallet.html'
    context_object_name = 'wallet'

    def get_object(self):
        """Get or create wallet for user"""
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add withdrawal form
        context['withdrawal_form'] = WalletWithdrawalForm()

        # Add recent transactions
        context['transactions'] = Transaction.objects.filter(
            wallet=self.object
        ).order_by('-created_at')[:10]

        # Add stats
        context['stats'] = {
            'total_deposits': self.object.total_deposited,
            'total_withdrawals': self.object.total_withdrawn,
            'total_transactions': context['transactions'].count(),
        }

        return context


class InitiateWithdrawalView(LoginRequiredMixin, CreateView):
    """
    Initiate wallet withdrawal
    """
    form_class = WalletWithdrawalForm
    template_name = 'payments/withdraw.html'
    success_url = reverse_lazy('payments:wallet')

    def get_form_kwargs(self):
        """Pass request user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Process valid withdrawal form"""
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=self.request.user)
                amount = form.cleaned_data['amount']

                # Check available balance
                if amount > wallet.available_balance:
                    messages.error(self.request,
                                   f'Insufficient funds. Available balance: KES {wallet.available_balance:,.2f}')
                    return self.form_invalid(form)

                # Create withdrawal transaction
                transaction_obj = Transaction.objects.create(
                    wallet=wallet,
                    user=self.request.user,
                    transaction_type='withdrawal',
                    amount=amount,
                    previous_balance=wallet.balance,
                    new_balance=wallet.balance - amount,
                    description=f'Withdrawal to {form.cleaned_data["method"]}',
                    reference=form.cleaned_data.get('account_details', '')
                )

                # Update wallet
                wallet.balance -= amount
                wallet.total_withdrawn += amount
                wallet.save()

                # Initiate M-Pesa payout if selected
                if form.cleaned_data['method'] == 'mpesa':
                    mpesa_client = MpesaClient()

                    result = mpesa_client.simulate_stk_push(
                        phone_number=self.request.user.profile.phone,
                        amount=amount,
                        account_reference=f'WDL{transaction_obj.id:06d}',
                        transaction_desc='Wallet withdrawal'
                    )

                    if result.get('success'):
                        messages.success(self.request,
                                         'Withdrawal initiated! Funds will be sent to your M-Pesa within 24 hours.')
                    else:
                        messages.warning(self.request,
                                         'Withdrawal recorded but M-Pesa transfer failed. Contact support.')
                else:
                    messages.success(self.request,
                                     'Withdrawal request submitted! It will be processed within 24 hours.')

                return redirect(self.success_url)

        except Exception as e:
            messages.error(self.request, f'Error processing withdrawal: {str(e)}')
            return self.form_invalid(form)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(TemplateView):
    """
    Handle M-Pesa callbacks (for STK Push results)
    This view is called by M-Pesa API
    """

    def post(self, request, *args, **kwargs):
        """Process M-Pesa callback"""
        from .mpesa.callbacks import process_mpesa_callback

        # Process the callback
        return process_mpesa_callback(request)


class PaymentHistoryView(LoginRequiredMixin, TemplateView):
    """
    View payment history with filters and stats
    """
    template_name = 'payments/history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get filter parameters
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')

        # Get payments
        payments = Payment.objects.filter(
            Q(payer=user) | Q(recipient=user)
        ).select_related('payer', 'recipient', 'project')

        # Apply date filters
        if year:
            payments = payments.filter(created_at__year=year)

        if month:
            payments = payments.filter(created_at__month=month)

        # Group by month for chart
        monthly_data = payments.extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(
            total_sent=Sum('amount', filter=Q(payer=user)),
            total_received=Sum('amount', filter=Q(recipient=user))
        ).order_by('month')

        context['payments'] = payments.order_by('-created_at')[:50]
        context['monthly_data'] = monthly_data
        context['total_payments'] = payments.count()

        # Calculate totals
        total_sent = payments.filter(payer=user, status='completed').aggregate(
            Sum('amount'))['amount__sum'] or 0

        total_received = payments.filter(recipient=user, status='completed').aggregate(
            Sum('amount'))['amount__sum'] or 0

        context['totals'] = {
            'sent': total_sent,
            'received': total_received,
            'net': total_received - total_sent,
        }

        return context


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """Payment success page"""
    template_name = 'payments/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get payment ID from URL or session
        payment_id = self.request.GET.get('payment') or self.request.session.get('last_payment_id')

        if payment_id:
            try:
                context['payment'] = Payment.objects.get(id=payment_id)
            except Payment.DoesNotExist:
                pass

        return context


class PaymentFailedView(LoginRequiredMixin, TemplateView):
    """Payment failed page"""
    template_name = 'payments/failed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get payment ID from URL or session
        payment_id = self.request.GET.get('payment') or self.request.session.get('last_payment_id')

        if payment_id:
            try:
                context['payment'] = Payment.objects.get(id=payment_id)
            except Payment.DoesNotExist:
                pass

        return context


# API Views for AJAX calls
@csrf_exempt
def check_payment_status(request, payment_id):
    """
    Check payment status (AJAX endpoint)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payment = Payment.objects.get(id=payment_id)

        # Check permissions
        if request.user not in [payment.payer, payment.recipient] and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Check M-Pesa status if applicable
        if payment.payment_method == 'mpesa' and payment.mpesa_code:
            mpesa_client = MpesaClient()
            result = mpesa_client.check_transaction_status(payment.mpesa_code)

            if result.get('success') and result.get('result_code') == '0':
                # Payment completed
                payment.status = 'completed'
                payment.save()

        return JsonResponse({
            'status': payment.status,
            'status_display': payment.get_status_display(),
            'amount': str(payment.amount),
            'created_at': payment.created_at.isoformat(),
        })

    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def retry_payment(request, payment_id):
    """
    Retry a failed payment (AJAX endpoint)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payment = Payment.objects.get(id=payment_id)

        # Check permissions and status
        if request.user != payment.payer:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        if payment.status not in ['failed', 'cancelled']:
            return JsonResponse({'error': 'Payment cannot be retried'}, status=400)

        # Retry M-Pesa payment
        if payment.payment_method == 'mpesa':
            mpesa_client = MpesaClient()

            if request.user.profile.phone:
                result = mpesa_client.stk_push(
                    phone_number=request.user.profile.phone,
                    amount=payment.amount,
                    account_reference=f"RETRY{payment.id:06d}",
                    transaction_desc=f"Retry: {payment.description[:50]}"
                )

                if result.get('success'):
                    payment.mpesa_code = result.get('checkout_request_id', '')
                    payment.status = 'processing'
                    payment.retry_count += 1
                    payment.save()

                    return JsonResponse({
                        'success': True,
                        'message': 'Payment retry initiated. Check your phone.',
                        'new_status': payment.status
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': result.get('error_message', 'Unknown error')
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number not found in profile'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Only M-Pesa payments can be retried automatically'
            })

    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

