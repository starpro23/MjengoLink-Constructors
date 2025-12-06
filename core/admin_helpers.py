# Create a helper file for mock data
def get_dashboard_stats():
    """Return mock dashboard statistics"""
    return {
        'verification_queue': 12,
        'active_disputes': 5,
        'completion_rate': 92,
        'new_users': 245,
        'active_projects': 156,
        'verification_turnaround': 18,
        'dispute_resolution_rate': 87,
        'platform_trust_score': 4.7,
        'fraud_rate': 0.8,
        'user_retention': 65,
        'approved_today': 8,
        'rejected_today': 2,
        'info_requested_today': 3,
        'avg_verification_time': 18.5,
        'approval_rate': 72,
        'fraud_detected': 3,
        'integrity_score': 8.2,
        'avg_processing_today': 15,
    }

def get_recent_activities():
    """Return mock recent activities"""
    return [
        {
            'priority': 'high',
            'icon': 'exclamation-triangle',
            'color': 'danger',
            'title': 'Payment dispute over KES 250,000 project',
            'description': 'Client claims incomplete work, artisan disputes quality standards',
            'category': 'Dispute',
            'time': '2 hours ago',
            'link': '#'
        },
        {
            'priority': 'medium',
            'icon': 'person-check',
            'color': 'warning',
            'title': 'Artisan verification request pending for 36 hours',
            'description': 'Documents submitted but reference checks incomplete',
            'category': 'Verification',
            'time': '3 hours ago',
            'link': '#'
        },
        {
            'priority': 'high',
            'icon': 'bell',
            'color': 'danger',
            'title': 'Multiple failed login attempts detected',
            'description': 'User account locked after 10 failed attempts from IP 192.168.1.100',
            'category': 'Security',
            'time': '4 hours ago',
            'link': '#'
        },
        {
            'priority': 'medium',
            'icon': 'chat-dots',
            'color': 'info',
            'title': 'Communication pattern anomaly detected',
            'description': 'Artisan sending same template messages to multiple clients',
            'category': 'Anomaly',
            'time': '5 hours ago',
            'link': '#'
        },
        {
            'priority': 'low',
            'icon': 'currency-exchange',
            'color': 'success',
            'title': 'Price beacon update recommended',
            'description': 'Electrician rates increased by 15% in Nairobi region',
            'category': 'Marketplace',
            'time': '6 hours ago',
            'link': '#'
        }
    ]

def get_verification_applications():
    """Return mock verification applications"""
    return[
        {
            'id': 1,
            'user': {
                'first_name': 'John',
                'last_name': 'Kamau',
                'username': 'JK001',
                'get_full_name': 'John Kamau',
                'profile': {
                    'location': 'Nairobi, Westlands'
                }
            },
            'trade': 'plumbing',
            'experience_years': 8,
            'documents': {
                'all': [
                    {'document_type': 'id_card', 'is_verified': True, 'is_rejected': False, 'get_status_display': 'Verified'},
                    {'document_type': 'certificate', 'is_verified': False, 'is_rejected': False, 'get_status_display': 'Pending'},
                    {'document_type': 'portfolio', 'is_verified': False, 'is_rejected': False, 'get_status_display': 'Pending'}
                ]
            },
            'references_verified': False,
            'references_pending': 2,
            'references_positive': 1,
            'integrity_score': 78,
            'risk_flags': 0,
            'queue_time_hours': 18,
            'created_at': '2024-01-15',
            'status': 'pending'
        },
        # Add more mock applications as needed
    ]