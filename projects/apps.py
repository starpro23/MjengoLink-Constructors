"""
Django App Configuration for Projects Application
Configures the projects app with proper settings and signals
"""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Configuration class for Projects app"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    verbose_name = 'Projects & Bids'

    def ready(self):
        """
        Import signals when app is ready
        This ensures signal handlers are connected
        """
        try:
            import projects.signals  # noqa F401
        except ImportError:
            pass


