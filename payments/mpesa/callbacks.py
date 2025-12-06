"""
M-Pesa Callback Handlers
Processes callbacks from M-Pesa API for:
- STK Push results
- Payment notifications
- Transaction status updates
"""

import json
import hashlib
import hmac
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from payments.models import Payment
from projects.models import Project
from django.utils import timezone


def validate_callback_signature(request):
    """
    Validate M-Pesa callback signature for security

    Args:
        request: Django HTTP request

    Returns:
        tuple: (is_valid, error_message)
    """
    # Get signature from headers
    signature = request.headers.get('X-MPesa-Signature', '')

    if not signature:
        return False, 'Missing signature'

    # Get validation key from settings
    validation_key = getattr(settings, 'MPESA_VALIDATION_KEY', '')

    if not validation_key:
        # In development, skip signature validation
        if settings.DEBUG:
            return True, 'Skipped in development'
        return False, 'Validation key not configured'

    # Calculate expected signature
    body = request.body.decode('utf-8')
    expected_signature = hmac.new(
        validation_key.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    if not hmac.compare_digest(signature, expected_signature):
        return False, 'Invalid signature'

    return True, 'Signature valid'


@csrf_exempt
@require_POST
def process_mpesa_callback(request):
    """
    Process M-Pesa callback (STK Push result)

    Expected JSON format from M-Pesa:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": "ws_CO_191220191020363925",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1},
                        {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                        {"Name": "TransactionDate", "Value": 20191219102115},
                        {"Name": "PhoneNumber", "Value": 254708374149}
                    ]
                }
            }
        }
    }
    """
    try:
        # Validate signature
        is_valid, error_msg = validate_callback_signature(request)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=400)

        # Parse JSON data
        data = json.loads(request.body)

        # Extract callback data
        stk_callback = data.get('Body', {}).get('stkCallback', {})

        merchant_request_id = stk_callback.get('MerchantRequestID', '')
        checkout_request_id = stk_callback.get('CheckoutRequestID', '')
        result_code = stk_callback.get('ResultCode', 1)  # 0 = success, other = error
        result_desc = stk_callback.get('ResultDesc', '')

        # Extract metadata
        callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])

        # Parse metadata into dictionary
        metadata = {}
        for item in callback_metadata:
            metadata[item.get('Name', '')] = item.get('Value', '')

        # Find payment by checkout request ID
        try:
            payment = Payment.objects.get(
                mpesa_code__icontains=checkout_request_id[:20]
            )
        except Payment.DoesNotExist:
            # Try to find by merchant request ID
            try:
                payment = Payment.objects.get(
                    transaction_reference__icontains=merchant_request_id[:20]
                )
            except Payment.DoesNotExist:
                # Log error and return success (MPesa expects 200 OK)
                print(f"Payment not found for callback: {checkout_request_id}")
                return JsonResponse({
                    'ResultCode': 0,
                    'ResultDesc': 'Callback received but payment not found'
                })

        # Update payment based on result code
        if result_code == 0:
            # Success
            payment.status = 'completed'
            payment.mpesa_receipt = metadata.get('MpesaReceiptNumber', '')
            payment.processed_at = timezone.now()
            payment.completed_at = timezone.now()
            payment.notes = f"M-Pesa callback: {result_desc}"

            # Extract additional data
            amount = metadata.get('Amount', 0)
            phone = metadata.get('PhoneNumber', '')

            if amount and payment.amount != amount:
                payment.notes += f" | Amount from callback: {amount}"

            if phone and not payment.mpesa_number:
                payment.mpesa_number = phone

            payment.save()

            # Update related project if applicable
            if payment.project and payment.milestone:
                milestone = payment.milestone
                milestone.status = 'paid'
                milestone.approved_at = timezone.now()
                milestone.save()

                # Check if all milestones are paid
                all_paid = all(
                    m.status == 'paid'
                    for m in payment.project.milestones.all()
                )

                if all_paid:
                    payment.project.status = 'completed'
                    payment.project.completed_at = timezone.now()
                    payment.project.save()

            print(f"Payment {payment.transaction_id} completed via M-Pesa")

        else:
            # Failure
            payment.status = 'failed'
            payment.failure_reason = result_desc
            payment.processed_at = timezone.now()
            payment.save()

            print(f"Payment {payment.transaction_id} failed: {result_desc}")

        # Return success response to M-Pesa
        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Success'
        })

    except json.JSONDecodeError as e:
        print(f"Invalid JSON in M-Pesa callback: {e}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Invalid JSON'
        }, status=400)

    except Exception as e:
        print(f"Error processing M-Pesa callback: {e}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': 'Server error'
        }, status=500)


def handle_b2c_callback(request):
    """
    Handle Business to Customer (B2C) callback
    For payments from business to customers (artisans)
    """
    # This would handle B2C callbacks (paying artisans)
    pass


def handle_c2b_validation(request):
    """
    Handle C2B (Customer to Business) validation callback
    Validates payment before processing
    """
    # This would validate C2B payments
    pass


def handle_c2b_confirmation(request):
    """
    Handle C2B (Customer to Business) confirmation callback
    Confirms payment after validation
    """
    # This would confirm C2B payments
    pass


def process_bulk_payment_callback(request):
    """
    Process bulk payment callback
    For multiple payments in one request
    """
    # This would handle bulk payment callbacks
    pass


