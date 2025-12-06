"""
M-Pesa Integration Module for Payments App
Handles all M-Pesa related operations:
- STK Push initiation and handling
- Callback processing
- Transaction status checking
- M-Pesa API client management
"""

# Make modules available at package level
from .client import MpesaClient
from .callbacks import process_mpesa_callback, validate_callback_signature

__all__ = [
    'MpesaClient',
    'process_mpesa_callback',
    'validate_callback_signature',
]
