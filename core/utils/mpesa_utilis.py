"""
M-Pesa Integration Utilities
Contains functions for M-Pesa API integration:
- STK Push initiation
- Payment validation
- Callback handling
- Transaction status checking
Note: This is a simulation for development. In production, you'd use actual Daraja API.
"""

import hashlib
import base64
import datetime
from django.conf import settings
import requests
import json
from urllib.parse import urlencode


class MpesaGateway:
    """M-Pesa API Gateway (Simulated for development)"""

    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')

        # Base URLs
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'

    def generate_access_token(self):
        """
        Generate OAuth access token for M-Pesa API

        Returns:
            str: Access token or empty string if failed
        """
        try:
            if not self.consumer_key or not self.consumer_secret:
                return ''

            # Encode consumer key and secret
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()

            # Make request
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            headers = {
                'Authorization': f'Basic {encoded_auth}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('access_token', '')
            else:
                print(f"MPesa token error: {response.status_code} - {response.text}")
                return ''

        except Exception as e:
            print(f"MPesa token generation error: {e}")
            return ''

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

    def simulate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Simulate STK Push request (for development/testing)

        Args:
            phone_number: Customer phone number (2547XXXXXXXX)
            amount: Transaction amount
            account_reference: Unique reference for the transaction
            transaction_desc: Description of the transaction

        Returns:
            dict: Simulated response with checkout request ID
        """
        # Generate timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Generate password
        password = self.generate_password(timestamp)

        # In development, simulate a response
        if settings.DEBUG:
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

        # In production, this would make actual API call
        access_token = self.generate_access_token()
        if not access_token:
            return {
                'success': False,
                'message': 'Failed to generate access token',
                'error_code': '401'
            }

        # Actual API call would go here
        # This is a placeholder for production implementation
        return {
            'success': False,
            'message': 'Production MPesa integration not configured',
            'error_code': '500'
        }

    def check_transaction_status(self, checkout_request_id):
        """
        Check status of an STK Push transaction

        Args:
            checkout_request_id: Checkout request ID from STK Push

        Returns:
            dict: Transaction status information
        """
        # In development, simulate status check
        if settings.DEBUG:
            # Simulate different statuses
            import random
            statuses = ['Pending', 'Completed', 'Failed', 'Cancelled']
            status = random.choice(statuses)

            return {
                'success': True,
                'checkout_request_id': checkout_request_id,
                'result_code': '0' if status == 'Completed' else '1032',
                'result_desc': f'Transaction {status.lower()}',
                'transaction_status': status,
                'simulated': True
            }

        # Production implementation would go here
        return {
            'success': False,
            'message': 'Production MPesa integration not configured',
            'error_code': '500'
        }

    def validate_callback_data(self, callback_data):
        """
        Validate M-Pesa callback data

        Args:
            callback_data: Dictionary of callback data from MPesa

        Returns:
            tuple: (is_valid, validated_data, error_message)
        """
        required_fields = ['Body', 'stkCallback']

        if not isinstance(callback_data, dict):
            return False, None, 'Callback data must be a dictionary'

        # Check for required fields
        for field in required_fields:
            if field not in callback_data:
                return False, None, f'Missing required field: {field}'

        try:
            # Extract relevant data
            stk_callback = callback_data['Body']['stkCallback']

            validated = {
                'merchant_request_id': stk_callback.get('MerchantRequestID', ''),
                'checkout_request_id': stk_callback.get('CheckoutRequestID', ''),
                'result_code': stk_callback.get('ResultCode', ''),
                'result_desc': stk_callback.get('ResultDesc', ''),
                'callback_metadata': stk_callback.get('CallbackMetadata', {}),
            }

            # Extract transaction details from metadata
            metadata = validated['callback_metadata'].get('Item', [])
            for item in metadata:
                if item.get('Name') == 'Amount':
                    validated['amount'] = item.get('Value', 0)
                elif item.get('Name') == 'MpesaReceiptNumber':
                    validated['mpesa_receipt'] = item.get('Value', '')
                elif item.get('Name') == 'TransactionDate':
                    validated['transaction_date'] = item.get('Value', '')
                elif item.get('Name') == 'PhoneNumber':
                    validated['phone_number'] = item.get('Value', '')

            return True, validated, None

        except Exception as e:
            return False, None, f'Error parsing callback data: {str(e)}'


def send_mpesa_stk_push(phone, amount, reference, description):
    """
    Convenience function to send STK Push

    Args:
        phone: Customer phone number
        amount: Amount to charge
        reference: Transaction reference
        description: Transaction description

    Returns:
        dict: Response from MPesa gateway
    """
    gateway = MpesaGateway()
    return gateway.simulate_stk_push(phone, amount, reference, description)


def format_phone_for_mpesa(phone_number):
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


def generate_mpesa_reference(user_id, project_id=None):
    """
    Generate unique reference for M-Pesa transactions

    Args:
        user_id: User ID
        project_id: Project ID (optional)

    Returns:
        str: Unique reference string
    """
    import time
    import hashlib

    timestamp = int(time.time())
    base_string = f"{user_id}_{timestamp}"

    if project_id:
        base_string += f"_{project_id}"

    # Create a short hash
    hash_obj = hashlib.md5(base_string.encode())
    short_hash = hash_obj.hexdigest()[:8].upper()

    return f"MJL{short_hash}"


