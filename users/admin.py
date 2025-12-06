"""
Admin interface configuration for Users app
Registers user models in Django admin for management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, ArtisanProfile, ArtisanDocument,
    ArtisanPortfolioImage, ArtisanReference, AdminActionLog, PlatformMetric
)


class UserProfileInline(admin.StackedInline):
    """Inline display for UserProfile in User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class ArtisanProfileInline(admin.StackedInline):
    """Inline display for ArtisanProfile in User admin"""
    model = ArtisanProfile
    can_delete = False
    verbose_name_plural = 'Artisan Details'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """Custom User admin with profile inlines"""
    inlines = [UserProfileInline, ArtisanProfileInline]
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'get_user_type']
    list_filter = ['profile__user_type', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'profile__phone']

    def get_user_type(self, obj):
        return obj.profile.user_type

    get_user_type.short_description = 'User Type'

    def get_inline_instances(self, request, obj=None):
        """Show ArtisanProfile inline only for artisans"""
        if not obj:
            return []

        inlines = [UserProfileInline(self.model, self.admin_site)]
        if hasattr(obj, 'profile') and obj.profile.user_type == 'artisan':
            inlines.append(ArtisanProfileInline(self.model, self.admin_site))
        return inlines


# Unregister default User admin and register custom
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(ArtisanDocument)
class ArtisanDocumentAdmin(admin.ModelAdmin):
    """Admin for Artisan Documents"""
    list_display = ['artisan', 'document_type', 'status', 'uploaded_at']
    list_filter = ['document_type', 'status']
    search_fields = ['artisan__email', 'artisan__first_name', 'artisan__last_name']
    list_editable = ['status']
    readonly_fields = ['uploaded_at', 'verified_at']


@admin.register(ArtisanPortfolioImage)
class ArtisanPortfolioImageAdmin(admin.ModelAdmin):
    """Admin for Artisan Portfolio Images"""
    list_display = ['artisan', 'caption', 'project_type', 'uploaded_at']
    list_filter = ['project_type']
    search_fields = ['artisan__email', 'caption', 'location']


@admin.register(ArtisanReference)
class ArtisanReferenceAdmin(admin.ModelAdmin):
    """Admin for Artisan References"""
    list_display = ['artisan', 'reference_name', 'relationship', 'rating', 'created_at']
    list_filter = ['relationship', 'rating']
    search_fields = ['artisan__email', 'reference_name', 'reference_phone']


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    """Admin for Admin Action Logs"""
    list_display = ['admin', 'action_type', 'target_user', 'created_at']
    list_filter = ['action_type']
    search_fields = ['admin__email', 'description', 'target_user__email']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']


@admin.register(PlatformMetric)
class PlatformMetricAdmin(admin.ModelAdmin):
    """Admin for Platform Metrics"""
    list_display = ['metric_type', 'value', 'period', 'recorded_at']
    list_filter = ['metric_type', 'period']
    readonly_fields = ['created_at']