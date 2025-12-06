"""
Users app configuration
Defines the users app and its configuration
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the users app
    Handles user profiles, artisan profiles, and authentication
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'User Management'

    def ready(self):
        """
        Import signals when app is ready
        """
        import users.signals