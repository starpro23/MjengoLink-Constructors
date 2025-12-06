"""
Test Suite for Payments App
Contains unit tests and integration tests for:
- Payment models and transactions
- M-Pesa integration
- Invoice generation
- Dispute handling
- Wallet operations
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from decimal import Decimal

from .models import Payment, Invoice, PaymentDispute, Wallet, Transaction
from projects.models import Project, ProjectMilestone
from users.models import UserProfile


class PaymentModelTest(TestCase):
    """Test cases for Payment model"""

    def setUp(self):
        """Create test users and payment"""
        self.payer = User.objects.create_user(
            username='payer',
            email='payer@example.com',
            password='testpass'
        )
        self.recipient = User.objects.create_user(
            username='recipient',
            email='recipient@example.com',
            password='testpass'
        )

        self.payment = Payment.objects.create(
            transaction_id='TEST123',
            payer=self.payer,
            recipient=self.recipient,
            amount=Decimal('1000.00'),
            payment_method='mpesa',
            payment_type='milestone',
            status='pending'
        )

    def test_payment_creation(self):
        """Test payment creation"""
        self.assertEqual(self.payment.payer.username, 'payer')
        self.assertEqual(self.payment.recipient.username, 'recipient')
        self.assertEqual(self.payment.amount, Decimal('1000.00'))
        self.assertEqual(self.payment.status, 'pending')

    def test_payment_str(self):
        """Test string representation"""
        expected = "Payment TEST123 - KES 1,000.00"
        self.assertEqual(str(self.payment), expected)

    def test_net_amount_calculation(self):
        """Test net amount calculation"""
        self.payment.service_fee = Decimal('50.00')
        self.payment.save()
        self.assertEqual(self.payment.net_amount, Decimal('950.00'))

    def test_transaction_id_generation(self):
        """Test automatic transaction ID generation"""
        payment = Payment.objects.create(
            payer=self.payer,
            recipient=self.recipient,
            amount=Decimal('500.00'),
            payment_method='bank'
        )
        self.assertTrue(payment.transaction_id.startswith('MJL-'))
        self.assertEqual(len(payment.transaction_id), 17)  # MJL- + 12 chars


class InvoiceModelTest(TestCase):
    """Test cases for Invoice model"""

    def setUp(self):
        """Create test users and invoice"""
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass'
        )
        self.artisan = User.objects.create_user(
            username='artisan',
            email='artisan@example.com',
            password='testpass'
        )

        self.invoice = Invoice.objects.create(
            invoice_number='INV-20240101-ABC123',
            client=self.client_user,
            artisan=self.artisan,
            amount=Decimal('5000.00'),
            description='Test invoice',
            due_date='2024-12-31'
        )

    def test_invoice_creation(self):
        """Test invoice creation"""
        self.assertEqual(self.invoice.client.username, 'client')
        self.assertEqual(self.invoice.artisan.username, 'artisan')
        self.assertEqual(self.invoice.amount, Decimal('5000.00'))
        self.assertEqual(self.invoice.status, 'draft')

    def test_invoice_str(self):
        """Test string representation"""
        expected = "Invoice INV-20240101-ABC123 - KES 5,000.00"
        self.assertEqual(str(self.invoice), expected)

    def test_total_amount_calculation(self):
        """Test total amount calculation"""
        self.invoice.tax_amount = Decimal('500.00')
        self.invoice.save()
        self.assertEqual(self.invoice.total_amount, Decimal('5500.00'))

    def test_invoice_number_generation(self):
        """Test automatic invoice number generation"""
        invoice = Invoice.objects.create(
            client=self.client_user,
            artisan=self.artisan,
            amount=Decimal('3000.00'),
            description='Auto-generated invoice'
        )
        self.assertTrue(invoice.invoice_number.startswith('INV-'))


class WalletModelTest(TestCase):
    """Test cases for Wallet model"""

    def setUp(self):
        """Create test user and wallet"""
        self.user = User.objects.create_user(
            username='walletuser',
            email='wallet@example.com',
            password='testpass'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('1000.00'),
            hold_balance=Decimal('200.00')
        )

    def test_wallet_creation(self):
        """Test wallet creation"""
        self.assertEqual(self.wallet.user.username, 'walletuser')
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))
        self.assertEqual(self.wallet.hold_balance, Decimal('200.00'))
        self.assertTrue(self.wallet.is_active)

    def test_wallet_str(self):
        """Test string representation"""
        expected = "Wallet: walletuser - KES 1,000.00"
        self.assertEqual(str(self.wallet), expected)

    def test_available_balance(self):
        """Test available balance calculation"""
        self.assertEqual(self.wallet.available_balance, Decimal('800.00'))

    def test_auto_wallet_creation(self):
        """Test automatic wallet creation for new user"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass'
        )
        self.assertTrue(hasattr(new_user, 'wallet'))
        self.assertEqual(new_user.wallet.balance, Decimal('0.00'))


class PaymentViewTests(TestCase):
    """Test cases for payment views"""

    def setUp(self):
        """Set up test client and users"""
        self.client = Client()
        self.payer = User.objects.create_user(
            username='testpayer',
            email='payer@example.com',
            password='testpass'
        )
        self.recipient = User.objects.create_user(
            username='testrecipient',
            email='recipient@example.com',
            password='testpass'
        )

        # Create user profiles with phone numbers
        UserProfile.objects.create(user=self.payer, phone='254712345678')
        UserProfile.objects.create(user=self.recipient, phone='254712345679')

        self.payment = Payment.objects.create(
            transaction_id='VIEWTEST123',
            payer=self.payer,
            recipient=self.recipient,
            amount=Decimal('1500.00'),
            status='pending'
        )

    def test_payment_list_view_authenticated(self):
        """Test payment list view for authenticated user"""
        self.client.login(username='testpayer', password='testpass')
        response = self.client.get(reverse('payments:payment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/payment_list.html')

    def test_payment_list_view_unauthenticated(self):
        """Test payment list view redirects for unauthenticated user"""
        response = self.client.get(reverse('payments:payment_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_payment_detail_view_authorized(self):
        """Test payment detail view for authorized user"""
        self.client.login(username='testpayer', password='testpass')
        response = self.client.get(reverse('payments:payment_detail', args=[self.payment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/payment_detail.html')

    def test_payment_detail_view_unauthorized(self):
        """Test payment detail view blocks unauthorized user"""
        unauthorized = User.objects.create_user(
            username='unauthorized',
            password='testpass'
        )
        self.client.login(username='unauthorized', password='testpass')
        response = self.client.get(reverse('payments:payment_detail', args=[self.payment.id]))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_payment_create_view_get(self):
        """Test payment create view GET"""
        self.client.login(username='testpayer', password='testpass')
        response = self.client.get(reverse('payments:payment_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/payment_create.html')


class MpesaIntegrationTests(TestCase):
    """Test cases for M-Pesa integration"""

    def test_phone_number_formatting(self):
        """Test phone number formatting for M-Pesa"""
        from payments.mpesa.client import MpesaClient

        client = MpesaClient()

        # Test various formats
        test_cases = [
            ('0712345678', '254712345678'),
            ('254712345678', '254712345678'),
            ('+254712345678', '254712345678'),
            ('712345678', '254712345678'),
            ('12345678', None),  # Too short
            ('25471234567890', None),  # Too long
        ]

        for input_phone, expected in test_cases:
            result = client.format_phone_number(input_phone)
            self.assertEqual(result, expected, f"Failed for {input_phone}")

    def test_password_generation(self):
        """Test M-Pesa password generation"""
        from payments.mpesa.client import MpesaClient

        client = MpesaClient()
        timestamp = '20240101120000'

        # Mock business shortcode and passkey
        client.business_shortcode = '174379'
        client.passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

        password = client.generate_password(timestamp)

        # Password should be base64 encoded
        import base64
        try:
            decoded = base64.b64decode(password).decode()
            self.assertTrue(decoded.startswith('174379'))
            self.assertTrue(timestamp in decoded)
        except:
            self.fail('Generated password is not valid base64')


class DisputeTests(TestCase):
    """Test cases for dispute handling"""

    def setUp(self):
        """Set up test data for disputes"""
        self.payer = User.objects.create_user(
            username='disputepayer',
            password='testpass'
        )
        self.recipient = User.objects.create_user(
            username='disputerecipient',
            password='testpass'
        )

        self.payment = Payment.objects.create(
            payer=self.payer,
            recipient=self.recipient,
            amount=Decimal('2000.00'),
            status='completed'
        )

    def test_dispute_creation(self):
        """Test dispute creation"""
        dispute = PaymentDispute.objects.create(
            dispute_id='DSP-TEST123',
            payment=self.payment,
            raised_by=self.payer,
            raised_against=self.recipient,
            title='Test Dispute',
            category='payment',
            severity='medium',
            description='Test dispute description'
        )

        self.assertEqual(dispute.raised_by, self.payer)
        self.assertEqual(dispute.raised_against, self.recipient)
        self.assertEqual(dispute.status, 'open')
        self.assertTrue(dispute.dispute_id.startswith('DSP-'))

    def test_dispute_evidence(self):
        """Test adding evidence to dispute"""
        dispute = PaymentDispute.objects.create(
            dispute_id='DSP-EVIDENCE',
            payment=self.payment,
            raised_by=self.payer,
            raised_against=self.recipient,
            title='Evidence Test',
            category='quality'
        )

        # Create evidence (file field would need mock in real test)
        evidence = DisputeEvidence.objects.create(
            dispute=dispute,
            uploaded_by=self.payer,
            evidence_type='document',
            description='Test evidence document'
        )

        self.assertEqual(evidence.dispute, dispute)
        self.assertEqual(evidence.uploaded_by, self.payer)
        self.assertEqual(evidence.evidence_type, 'document')


class TransactionTests(TestCase):
    """Test cases for wallet transactions"""

    def setUp(self):
        """Set up test wallet and user"""
        self.user = User.objects.create_user(
            username='transactionuser',
            password='testpass'
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('5000.00')
        )

    def test_deposit_transaction(self):
        """Test deposit transaction creation"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            user=self.user,
            transaction_type='deposit',
            amount=Decimal('1000.00'),
            previous_balance=Decimal('5000.00'),
            new_balance=Decimal('6000.00'),
            description='Test deposit'
        )

        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.transaction_type, 'deposit')
        self.assertEqual(transaction.amount, Decimal('1000.00'))
        self.assertTrue(transaction.transaction_id.startswith('WLT-'))

        # Check wallet balance updated (though transaction doesn't auto-update wallet)
        self.wallet.balance = transaction.new_balance
        self.wallet.save()
        self.assertEqual(self.wallet.balance, Decimal('6000.00'))

    def test_withdrawal_transaction(self):
        """Test withdrawal transaction creation"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            user=self.user,
            transaction_type='withdrawal',
            amount=Decimal('2000.00'),
            previous_balance=Decimal('5000.00'),
            new_balance=Decimal('3000.00'),
            description='Test withdrawal'
        )

        self.assertEqual(transaction.transaction_type, 'withdrawal')
        self.assertEqual(transaction.amount, Decimal('2000.00'))


# Run all tests
if __name__ == '__main__':
    import unittest

    unittest.main()
