"""
Django App Configuration for Core Application
Configures the core app with proper settings and signals
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration class for Core app"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Site Management'

    def ready(self):
        """
        Import signals when app is ready
        This ensures signal handlers are connected
        """
        try:
            import core.signals  # noqa F401
        except ImportError:
            pass


