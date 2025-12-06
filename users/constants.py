"""
Constants and Configuration for Users App
Centralized constants for user types, trades, document types, etc.
"""

# User Types
USER_TYPES = {
    'HOMEOWNER': 'homeowner',
    'ARTISAN': 'artisan',
    'ADMIN': 'admin',
    'MODERATOR': 'moderator',
}

# Trade Categories
TRADE_CATEGORIES = {
    'PLUMBING': 'plumbing',
    'ELECTRICAL': 'electrical',
    'MASONRY': 'masonry',
    'CARPENTRY': 'carpentry',
    'PAINTING': 'painting',
    'WELDING': 'welding',
    'ROOFING': 'roofing',
    'TILING': 'tiling',
    'LANDSCAPING': 'landscaping',
    'INTERIOR_DESIGN': 'interior_design',
    'PLASTERING': 'plastering',
    'METALWORK': 'metalwork',
    'GLASS_WORK': 'glass_work',
    'FLOORING': 'flooring',
    'FENCING': 'fencing',
    'GENERAL_CONTRACTOR': 'general_contractor',
    'HVAC': 'hvac',
    'CONCRETE': 'concrete',
    'STEEL_WORK': 'steel_work',
    'OTHER': 'other',
}

# Document Types for Verification
DOCUMENT_TYPES = {
    'ID_CARD': 'id_card',
    'PASSPORT': 'passport',
    'CERTIFICATE': 'certificate',
    'LICENSE': 'license',
    'PORTFOLIO': 'portfolio',
    'REFERENCE': 'reference',
    'INSURANCE': 'insurance',
    'TAX_CERTIFICATE': 'tax_certificate',
    'BUSINESS_REGISTRATION': 'business_registration',
    'HEALTH_CERTIFICATE': 'health_certificate',
}

# Verification Status
VERIFICATION_STATUS = {
    'PENDING': 'pending',
    'UNDER_REVIEW': 'under_review',
    'VERIFIED': 'verified',
    'REJECTED': 'rejected',
    'NEEDS_REVISION': 'needs_revision',
    'EXPIRED': 'expired',
}

# Admin Action Types
ADMIN_ACTION_TYPES = {
    'USER_VERIFICATION': 'user_verification',
    'DOCUMENT_APPROVAL': 'document_approval',
    'DISPUTE_RESOLUTION': 'dispute_resolution',
    'USER_SUSPENSION': 'user_suspension',
    'CONTENT_MODERATION': 'content_moderation',
    'PAYMENT_RELEASE': 'payment_release',
    'PLATFORM_UPDATE': 'platform_update',
    'SECURITY_ALERT': 'security_alert',
    'SYSTEM_MAINTENANCE': 'system_maintenance',
}

# Platform Metric Types
METRIC_TYPES = {
    'VERIFICATION_TURNAROUND': 'verification_turnaround',
    'DISPUTE_RESOLUTION_RATE': 'dispute_resolution_rate',
    'PLATFORM_TRUST_SCORE': 'platform_trust_score',
    'USER_RETENTION_RATE': 'user_retention_rate',
    'TRANSACTION_VOLUME': 'transaction_volume',
    'ACTIVE_USERS': 'active_users',
    'NEW_SIGNUPS': 'new_signups',
    'PROJECT_COMPLETION_RATE': 'project_completion_rate',
    'FRAUD_PREVENTION_RATE': 'fraud_prevention_rate',
    'USER_SATISFACTION_SCORE': 'user_satisfaction_score',
    'REVENUE': 'revenue',
    'COMMISSION_EARNED': 'commission_earned',
}

# User Status
USER_STATUS = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'SUSPENDED': 'suspended',
    'BANNED': 'banned',
    'PENDING_VERIFICATION': 'pending_verification',
    'UNDER_REVIEW': 'under_review',
}

# Notification Types
NOTIFICATION_TYPES = {
    'VERIFICATION_APPROVED': 'verification_approved',
    'VERIFICATION_REJECTED': 'verification_rejected',
    'NEW_MESSAGE': 'new_message',
    'BID_ACCEPTED': 'bid_accepted',
    'BID_REJECTED': 'bid_rejected',
    'MILESTONE_COMPLETED': 'milestone_completed',
    'PAYMENT_RECEIVED': 'payment_received',
    'PROJECT_ASSIGNED': 'project_assigned',
    'REVIEW_RECEIVED': 'review_received',
    'SYSTEM_ANNOUNCEMENT': 'system_announcement',
    'SECURITY_ALERT': 'security_alert',
}

# Location Zones for Kenya
LOCATION_ZONES = {
    'NAIROBI': 'Nairobi',
    'MOMBASA': 'Mombasa',
    'KISUMU': 'Kisumu',
    'NAKURU': 'Nakuru',
    'ELDORET': 'Eldoret',
    'THIKA': 'Thika',
    'MALINDI': 'Malindi',
    'KITALE': 'Kitale',
    'GARISSA': 'Garissa',
    'KAKAMEGA': 'Kakamega',
    'OTHER': 'Other',
}

# Experience Levels
EXPERIENCE_LEVELS = {
    'BEGINNER': (0, 2, '0-2 years'),
    'INTERMEDIATE': (3, 5, '3-5 years'),
    'EXPERIENCED': (6, 10, '6-10 years'),
    'EXPERT': (11, 20, '11-20 years'),
    'MASTER': (21, 50, '20+ years'),
}

# Rating Categories
RATING_CATEGORIES = {
    'QUALITY': 'quality',
    'TIMELINESS': 'timeliness',
    'COMMUNICATION': 'communication',
    'PROFESSIONALISM': 'professionalism',
    'VALUE': 'value',
}