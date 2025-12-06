"""
Security Utilities for Core App
Contains security-related functions:
- Password hashing and validation
- Token generation
- Input sanitization
- XSS prevention
- CSRF protection helpers
"""

import hashlib
import secrets
import string
import re
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import html


def generate_secure_token(length=32):
    """
    Generate cryptographically secure random token

    Args:
        length: Length of token in characters

    Returns:
        str: Secure random token
    """
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    return token


def hash_password(password, salt=None):
    """
    Hash password with salt (for manual password handling if needed)

    Args:
        password: Plain text password
        salt: Salt string (if None, generates new salt)

    Returns:
        tuple: (hashed_password, salt)
    """
    if salt is None:
        salt = generate_secure_token(16)

    # Combine password and salt
    combined = f"{password}{salt}"

    # Hash using SHA256 (in production, use Django's built-in password hashing)
    hashed = hashlib.sha256(combined.encode()).hexdigest()

    return hashed, salt


def validate_password_strength(password):
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    # Check for common passwords (simplified)
    common_passwords = [
        'password', '12345678', 'qwerty', 'admin', 'welcome',
        'password123', 'abc123', 'letmein', 'monkey', 'sunshine'
    ]

    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password."

    return True, "Password is strong"


def sanitize_input(input_string, allow_html=False):
    """
    Sanitize user input to prevent XSS attacks

    Args:
        input_string: String to sanitize
        allow_html: Whether to allow HTML tags (use with caution!)

    Returns:
        str: Sanitized string
    """
    if not input_string:
        return ''

    # Convert to string if not already
    if not isinstance(input_string, str):
        input_string = str(input_string)

    # Strip whitespace
    input_string = input_string.strip()

    if allow_html:
        # Allow limited HTML but escape dangerous tags
        # This is a simplified version - in production, use a library like bleach
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'link', 'meta']
        for tag in dangerous_tags:
            pattern = re.compile(f'<{tag}.*?>.*?</{tag}>', re.IGNORECASE | re.DOTALL)
            input_string = pattern.sub('', input_string)

        # Also remove inline event handlers
        input_string = re.sub(r'on\w+=".*?"', '', input_string)
        input_string = re.sub(r"on\w+='.*?'", '', input_string)
    else:
        # Strip all HTML tags
        input_string = strip_tags(input_string)

    # Escape special characters
    input_string = html.escape(input_string)

    return input_string


def generate_csrf_token():
    """
    Generate CSRF token (alternative to Django's built-in)

    Returns:
        str: CSRF token
    """
    return secrets.token_urlsafe(32)


def validate_csrf_token(token, session_token):
    """
    Validate CSRF token

    Args:
        token: Token from request
        session_token: Token stored in session

    Returns:
        bool: True if valid
    """
    if not token or not session_token:
        return False

    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(token, session_token)


def generate_expiry_date(days=7):
    """
    Generate expiry date for tokens

    Args:
        days: Number of days until expiry

    Returns:
        datetime: Expiry datetime
    """
    return datetime.now() + timedelta(days=days)


def is_token_expired(expiry_date):
    """
    Check if token is expired

    Args:
        expiry_date: Datetime to check

    Returns:
        bool: True if expired
    """
    if not expiry_date:
        return True

    return datetime.now() > expiry_date


def mask_sensitive_data(data, visible_chars=4):
    """
    Mask sensitive data for logging (e.g., email, phone)

    Args:
        data: Sensitive string
        visible_chars: Number of ending characters to show

    Returns:
        str: Masked string
    """
    if not data or len(data) <= visible_chars:
        return '*' * len(data) if data else ''

    # Show only last n characters, mask the rest
    masked_length = len(data) - visible_chars
    return '*' * masked_length + data[-visible_chars:]


def validate_file_upload(file, allowed_types=None, max_size_mb=10):
    """
    Validate file upload for security

    Args:
        file: Django UploadedFile object
        allowed_types: List of allowed MIME types or extensions
        max_size_mb: Maximum file size in MB

    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"

    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        return False, f"File too large. Maximum size is {max_size_mb}MB"

    # Check file type
    if allowed_types:
        import mimetypes
        file_type = mimetypes.guess_type(file.name)[0]

        if not file_type:
            # Try to get from name
            ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
            if ext not in allowed_types:
                return False, f"File type not allowed. Allowed: {', '.join(allowed_types)}"
        elif file_type not in allowed_types:
            # Check if any extension matches
            ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
            if ext not in allowed_types:
                return False, f"File type not allowed. Allowed: {', '.join(allowed_types)}"

    # Check for null bytes (potential security issue)
    if b'\x00' in file.name.encode():
        return False, "Invalid file name"

    return True, "File validated successfully"


def generate_secure_filename(original_filename):
    """
    Generate secure filename to prevent path traversal

    Args:
        original_filename: Original filename

    Returns:
        str: Secure filename
    """
    import os
    import uuid

    # Get file extension
    ext = os.path.splitext(original_filename)[1].lower()

    # Generate secure name
    secure_name = f"{uuid.uuid4().hex}{ext}"

    return secure_name


