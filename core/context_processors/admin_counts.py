def admin_counts(request):
    """Context processor for admin counts"""
    if request.user.is_authenticated and request.user.is_staff:
        # In production, these would come from your database
        # For now, we'll use mock data
        return {
            'verification_count': 12,
            'dispute_count': 5,
            'anomaly_count': 3,
            'active_users_count': 2456,
        }
    return {}
