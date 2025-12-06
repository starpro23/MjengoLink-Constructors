"""
URL Configuration for Payments App
Defines URL patterns for:
- Payment processing and management
- Invoice handling
- Dispute resolution
- Wallet operations
- M-Pesa integration callbacks
"""

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views
from .mpesa.callbacks import process_mpesa_callback

app_name = 'payments'

urlpatterns = [
    # Payment Management
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path('create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('history/', views.PaymentHistoryView.as_view(), name='history'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('failed/', views.PaymentFailedView.as_view(), name='failed'),

    # Invoice Management
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),

    # Dispute Management
    path('disputes/create/', views.DisputeCreateView.as_view(), name='dispute_create'),
    path('disputes/<int:pk>/', views.DisputeDetailView.as_view(), name='dispute_detail'),
    path('disputes/<int:dispute_id>/evidence/add/', views.AddEvidenceView.as_view(), name='add_evidence'),

    # Wallet Management
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    path('wallet/withdraw/', views.InitiateWithdrawalView.as_view(), name='withdraw'),

    # M-Pesa Integration
    path('mpesa/callback/', csrf_exempt(views.MpesaCallbackView.as_view()), name='mpesa_callback'),

    # API Endpoints (AJAX)
    path('api/payment/<int:payment_id>/status/', views.check_payment_status, name='check_payment_status'),
    path('api/payment/<int:payment_id>/retry/', views.retry_payment, name='retry_payment'),
]
