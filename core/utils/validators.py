"""
Validation Utilities for Core App
Contains data validation functions:
- Form field validation
- Business logic validation
- Input format checking
- Data integrity validation
"""

import re
import phonenumbers
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value, country='KE'):
    """
    Validate phone number using phonenumbers library

    Args:
        value: Phone number string
        country: Country code (default: Kenya)

    Returns:
        str: Validated phone number in E.164 format

    Raises:
        ValidationError: If phone number is invalid
    """
    if not value:
        raise ValidationError(_('Phone number is required'))

    try:
        # Parse phone number
        phone = phonenumbers.parse(value, country)

        # Check if valid
        if not phonenumbers.is_valid_number(phone):
            raise ValidationError(_('Invalid phone number'))

        # Format in E.164 format
        formatted = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)

        return formatted

    except phonenumbers.NumberParseException:
        raise ValidationError(_('Invalid phone number format'))


def validate_email(value):
    """
    Validate email address format

    Args:
        value: Email address string

    Returns:
        str: Validated email

    Raises:
        ValidationError: If email is invalid
    """
    if not value:
        raise ValidationError(_('Email address is required'))

    # Basic regex validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_regex, value):
        raise ValidationError(_('Enter a valid email address'))

    # Check for disposable email domains (simplified)
    disposable_domains = [
        'tempmail.com', 'guerrillamail.com', 'mailinator.com',
        'sharklasers.com', 'grr.la', 'guerrillamail.net'
    ]

    domain = value.split('@')[1].lower()
    if domain in disposable_domains:
        raise ValidationError(_('Disposable email addresses are not allowed'))

    return value


def validate_name(value, field_name='Name'):
    """
    Validate person name

    Args:
        value: Name string
        field_name: Field name for error messages

    Returns:
        str: Validated name

    Raises:
        ValidationError: If name is invalid
    """
    if not value:
        raise ValidationError(_(f'{field_name} is required'))

    # Remove extra whitespace
    value = ' '.join(value.strip().split())

    # Check length
    if len(value) < 2:
        raise ValidationError(_(f'{field_name} must be at least 2 characters long'))

    if len(value) > 100:
        raise ValidationError(_(f'{field_name} cannot exceed 100 characters'))

    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r'^[A-Za-z\s\-\'\.]+$', value):
        raise ValidationError(_(f'{field_name} can only contain letters, spaces, hyphens, apostrophes, and periods'))

    # Check for consecutive special characters
    if re.search(r'[\-\'\\.]{2,}', value):
        raise ValidationError(_(f'{field_name} cannot have consecutive special characters'))

    return value


def validate_password(value):
    """
    Validate password strength

    Args:
        value: Password string

    Returns:
        str: Validated password

    Raises:
        ValidationError: If password is invalid
    """
    if not value:
        raise ValidationError(_('Password is required'))

    # Check length
    if len(value) < 8:
        raise ValidationError(_('Password must be at least 8 characters long'))

    if len(value) > 128:
        raise ValidationError(_('Password cannot exceed 128 characters'))

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', value):
        raise ValidationError(_('Password must contain at least one uppercase letter'))

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', value):
        raise ValidationError(_('Password must contain at least one lowercase letter'))

    # Check for at least one digit
    if not re.search(r'\d', value):
        raise ValidationError(_('Password must contain at least one digit'))

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError(_('Password must contain at least one special character'))

    return value


def validate_username(value):
    """
    Validate username

    Args:
        value: Username string

    Returns:
        str: Validated username

    Raises:
        ValidationError: If username is invalid
    """
    if not value:
        raise ValidationError(_('Username is required'))

    # Check length
    if len(value) < 3:
        raise ValidationError(_('Username must be at least 3 characters long'))

    if len(value) > 30:
        raise ValidationError(_('Username cannot exceed 30 characters'))

    # Check for valid characters
    if not re.match(r'^[a-zA-Z0-9_\.]+$', value):
        raise ValidationError(_('Username can only contain letters, numbers, underscores, and periods'))

    # Check if starts with letter
    if not re.match(r'^[a-zA-Z]', value):
        raise ValidationError(_('Username must start with a letter'))

    # Check for reserved usernames
    reserved = ['admin', 'administrator', 'root', 'system', 'support',
                'info', 'contact', 'help', 'test', 'user']

    if value.lower() in reserved:
        raise ValidationError(_('This username is not available'))

    return value


def validate_date(value, min_date=None, max_date=None):
    """
    Validate date

    Args:
        value: Date string or datetime object
        min_date: Minimum allowed date
        max_date: Maximum allowed date

    Returns:
        date: Validated date

    Raises:
        ValidationError: If date is invalid
    """
    if not value:
        raise ValidationError(_('Date is required'))

    # Convert to date if it's a datetime
    if isinstance(value, datetime):
        value = value.date()

    if not isinstance(value, date):
        try:
            # Try to parse string
            if isinstance(value, str):
                value = datetime.strptime(value, '%Y-%m-%d').date()
            else:
                raise ValidationError(_('Invalid date format'))
        except ValueError:
            raise ValidationError(_('Invalid date format. Use YYYY-MM-DD'))

    # Check if date is in the past (for birth dates, etc.)
    if value > date.today():
        raise ValidationError(_('Date cannot be in the future'))

    # Check minimum date
    if min_date and value < min_date:
        raise ValidationError(_(f'Date must be on or after {min_date.strftime("%Y-%m-%d")}'))

    # Check maximum date
    if max_date and value > max_date:
        raise ValidationError(_(f'Date must be on or before {max_date.strftime("%Y-%m-%d")}'))

    return value


def validate_amount(value, min_amount=0.01, max_amount=10000000):
    """
    Validate monetary amount

    Args:
        value: Amount (can be string, int, or float)
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount

    Returns:
        float: Validated amount

    Raises:
        ValidationError: If amount is invalid
    """
    if value is None:
        raise ValidationError(_('Amount is required'))

    try:
        # Convert to float
        if isinstance(value, str):
            value = float(value.replace(',', ''))
        else:
            value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(_('Invalid amount'))

    # Check range
    if value < min_amount:
        raise ValidationError(_(f'Amount must be at least {min_amount}'))

    if value > max_amount:
        raise ValidationError(_(f'Amount cannot exceed {max_amount}'))

    # Check decimal places
    if not (0 <= value - int(value) < 1):
        raise ValidationError(_('Amount can have up to 2 decimal places'))

    return round(value, 2)


def validate_location(value):
    """
    Validate location string

    Args:
        value: Location string

    Returns:
        str: Validated location

    Raises:
        ValidationError: If location is invalid
    """
    if not value:
        raise ValidationError(_('Location is required'))

    value = value.strip()

    # Check length
    if len(value) < 3:
        raise ValidationError(_('Location must be at least 3 characters long'))

    if len(value) > 200:
        raise ValidationError(_('Location cannot exceed 200 characters'))

    # Check for valid characters (allow letters, numbers, spaces, commas, hyphens)
    if not re.match(r'^[A-Za-z0-9\s,\-\.]+$', value):
        raise ValidationError(_('Location can only contain letters, numbers, spaces, commas, hyphens, and periods'))

    return value


def validate_id_number(value, country='KE'):
    """
    Validate national ID number (Kenya specific)

    Args:
        value: ID number string
        country: Country code

    Returns:
        str: Validated ID number

    Raises:
        ValidationError: If ID number is invalid
    """
    if not value:
        raise ValidationError(_('ID number is required'))

    value = value.strip().upper()

    if country == 'KE':
        # Kenya ID validation (simplified)
        # Format: 8 digits (old) or 1 letter + 8 digits (new)

        if len(value) not in [8, 9]:
            raise ValidationError(_('ID number must be 8 or 9 characters'))

        if len(value) == 9:
            # New format: 1 letter + 8 digits
            if not (value[0].isalpha() and value[1:].isdigit()):
                raise ValidationError(_('Invalid ID number format. Expected: 1 letter followed by 8 digits'))
        else:
            # Old format: 8 digits
            if not value.isdigit():
                raise ValidationError(_('ID number must contain only digits'))

    return value


def validate_postal_code(value, country='KE'):
    """
    Validate postal code

    Args:
        value: Postal code string
        country: Country code

    Returns:
        str: Validated postal code

    Raises:
        ValidationError: If postal code is invalid
    """
    if not value:
        return value  # Postal code can be optional

    value = value.strip()

    if country == 'KE':
        # Kenya postal codes: 5 digits
        if not re.match(r'^\d{5}$', value):
            raise ValidationError(_('Postal code must be 5 digits'))

    return value


def validate_url(value, require_https=False):
    """
    Validate URL

    Args:
        value: URL string
        require_https: Whether to require HTTPS

    Returns:
        str: Validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not value:
        return value  # URL can be optional

    value = value.strip()

    # Basic URL validation
    url_regex = r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'

    if not re.match(url_regex, value):
        raise ValidationError(_('Enter a valid URL'))

    if require_https and not value.startswith('https://'):
        raise ValidationError(_('URL must use HTTPS'))

    return value


def validate_text_length(value, field_name, min_length=1, max_length=5000):
    """
    Validate text length

    Args:
        value: Text string
        field_name: Field name for error messages
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        str: Validated text

    Raises:
        ValidationError: If text length is invalid
    """
    if not value and min_length > 0:
        raise ValidationError(_(f'{field_name} is required'))

    if value:
        value = value.strip()

        if len(value) < min_length:
            raise ValidationError(_(f'{field_name} must be at least {min_length} characters long'))

        if len(value) > max_length:
            raise ValidationError(_(f'{field_name} cannot exceed {max_length} characters'))

    return value


