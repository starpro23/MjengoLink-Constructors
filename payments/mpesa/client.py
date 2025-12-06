"""
M-Pesa API Client
Handles communication with Safaricom M-Pesa API
Contains methods for:
- Authentication and token management
- STK Push initiation
- Transaction status queries
- Account balance queries
"""

import base64
import datetime
import hashlib
import requests
import json
from urllib.parse import urljoin
from django.conf import settings
from django.utils import timezone


class MpesaClient:
    """
    M-Pesa API Client for interacting with Safaricom Daraja API
    """

    def __init__(self, environment=None):
        """
        Initialize M-Pesa client

        Args:
            environment: 'sandbox' or 'production'. Defaults from settings
        """
        self.environment = environment or getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')

        # Load configuration from settings
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        self.initiator_name = getattr(settings, 'MPESA_INITIATOR_NAME', '')
        self.security_credential = getattr(settings, 'MPESA_SECURITY_CREDENTIAL', '')

        # Set base URLs based on environment
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'

        # Initialize session and token
        self.session = requests.Session()
        self.access_token = None
        self.token_expiry = None

    def get_access_token(self):
        """
        Get OAuth access token for M-Pesa API

        Returns:
            str: Access token or None if failed
        """
        # Check if token is still valid
        if self.access_token and self.token_expiry:
            if timezone.now() < self.token_expiry:
                return self.access_token

        # Generate new token
        url = urljoin(self.base_url, '/oauth/v1/generate?grant_type=client_credentials')

        # Create auth string
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        }

        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get('access_token')

            # Set expiry (token expires in 1 hour, set to 50 minutes for safety)
            self.token_expiry = timezone.now() + datetime.timedelta(minutes=50)

            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"Error getting M-Pesa access token: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return None

    def generate_password(self, timestamp):
        """
        Generate password for STK Push

        Args:
            timestamp: Transaction timestamp in format YYYYMMDDHHMMSS

        Returns:
            str: Base64 encoded password
        """
        data_to_encode = f"{self.business_shortcode}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode()).decode()
        return encoded

    def format_phone_number(self, phone_number):
        """
        Format phone number for M-Pesa (2547XXXXXXXX format)

        Args:
            phone_number: Phone number in any format

        Returns:
            str: Formatted phone number or None if invalid
        """
        import re

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_number)

        # Check length
        if len(digits) < 9 or len(digits) > 12:
            return None

        # Format to 254 format
        if digits.startswith('0'):
            # Convert 07... to 2547...
            return '254' + digits[1:]
        elif digits.startswith('254'):
            # Already in correct format
            return digits
        elif len(digits) == 9:
            # Assume it's missing 254 prefix
            return '254' + digits
        else:
            return None

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push (Customer to Business)

        Args:
            phone_number: Customer phone number
            amount: Amount to charge
            account_reference: Unique reference for the transaction
            transaction_desc: Description of the transaction

        Returns:
            dict: Response from M-Pesa API
        """
        # Get access token
        token = self.get_access_token()
        if not token:
            return {
                'success': False,
                'error_code': 'AUTH_FAILED',
                'error_message': 'Failed to authenticate with M-Pesa API'
            }

        # Format phone number
        formatted_phone = self.format_phone_number(phone_number)
        if not formatted_phone:
            return {
                'success': False,
                'error_code': 'INVALID_PHONE',
                'error_message': 'Invalid phone number format'
            }

        # Generate timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Generate password
        password = self.generate_password(timestamp)

        # Prepare request payload
        payload = {
            "BusinessShortCode": self.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),  # Amount in whole shillings
            "PartyA": formatted_phone,
            "PartyB": self.business_shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        # Make API request
        url = urljoin(self.base_url, '/mpesa/stkpush/v1/processrequest')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Parse response
            if data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'merchant_request_id': data.get('MerchantRequestID'),
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'response_code': data.get('ResponseCode'),
                    'response_description': data.get('ResponseDescription'),
                    'customer_message': data.get('CustomerMessage'),
                    'timestamp': timestamp
                }
            else:
                return {
                    'success': False,
                    'error_code': data.get('ResponseCode', 'UNKNOWN'),
                    'error_message': data.get('ResponseDescription', 'Unknown error'),
                    'customer_message': data.get('CustomerMessage', '')
                }

        except requests.exceptions.RequestException as e:
            print(f"Error initiating STK Push: {e}")
            error_message = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('errorMessage', str(e))
                except:
                    error_message = e.response.text

            return {
                'success': False,
                'error_code': 'REQUEST_FAILED',
                'error_message': error_message
            }

    def check_transaction_status(self, checkout_request_id):
        """
        Check status of an STK Push transaction

        Args:
            checkout_request_id: Checkout request ID from STK Push

        Returns:
            dict: Transaction status information
        """
        # Get access token
        token = self.get_access_token()
        if not token:
            return {
                'success': False,
                'error_code': 'AUTH_FAILED',
                'error_message': 'Failed to authenticate with M-Pesa API'
            }

        # Generate timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Generate password
        password = self.generate_password(timestamp)

        # Prepare request payload
        payload = {
            "BusinessShortCode": self.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        # Make API request
        url = urljoin(self.base_url, '/mpesa/stkpushquery/v1/query')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'response_code': data.get('ResponseCode'),
                'response_description': data.get('ResponseDescription'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'checkout_request_id': data.get('CheckoutRequestID'),
                'result_code': data.get('ResultCode'),
                'result_description': data.get('ResultDesc')
            }

        except requests.exceptions.RequestException as e:
            print(f"Error checking transaction status: {e}")
            return {
                'success': False,
                'error_code': 'REQUEST_FAILED',
                'error_message': str(e)
            }

    def simulate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Simulate STK Push for development/testing

        Args:
            phone_number: Customer phone number
            amount: Amount to charge
            account_reference: Unique reference for the transaction
            transaction_desc: Description of the transaction

        Returns:
            dict: Simulated response
        """
        # For development/testing, simulate a successful response
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        return {
            'success': True,
            'message': 'STK Push simulated successfully',
            'checkout_request_id': f'ws_CO_{timestamp}_{account_reference}',
            'merchant_request_id': f'1000-{timestamp}-{account_reference}',
            'response_code': '0',
            'response_description': 'Success. Request accepted for processing',
            'customer_message': 'Success. Request accepted for processing',
            'simulated': True,
            'timestamp': timestamp
        }

    def get_account_balance(self):
        """
        Get business account balance

        Returns:
            dict: Account balance information
        """
        # This is a placeholder for account balance query
        # Actual implementation would require additional permissions
        token = self.get_access_token()
        if not token:
            return {
                'success': False,
                'error_code': 'AUTH_FAILED',
                'error_message': 'Failed to authenticate with M-Pesa API'
            }

        # Note: Actual implementation would make API call here
        return {
            'success': False,
            'error_code': 'NOT_IMPLEMENTED',
            'error_message': 'Account balance query not implemented'
        }

    def reverse_transaction(self, transaction_id, amount):
        """
        Reverse a transaction

        Args:
            transaction_id: Original transaction ID
            amount: Amount to reverse

        Returns:
            dict: Reversal response
        """
        # This is a placeholder for transaction reversal
        token = self.get_access_token()
        if not token:
            return {
                'success': False,
                'error_code': 'AUTH_FAILED',
                'error_message': 'Failed to authenticate with M-Pesa API'
            }

        # Note: Actual implementation would make API call here
        return {
            'success': False,
            'error_code': 'NOT_IMPLEMENTED',
            'error_message': 'Transaction reversal not implemented'
        }


