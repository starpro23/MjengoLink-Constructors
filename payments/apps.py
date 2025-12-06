"""
Django App Configuration for Payments Application
Configures the payments app with proper settings and signals
"""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuration class for Payments app"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Payments & Transactions'

    def ready(self):
        """
        Import signals when app is ready
        This ensures signal handlers are connected
        """
        try:
            import payments.signals  # noqa F401
        except ImportError:
            pass


