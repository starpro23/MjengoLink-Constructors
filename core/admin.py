"""
Django Admin Configuration for Core App
Contains admin interfaces for:
- Site settings management
- Contact message handling
- Testimonial management
- FAQ administration
- Newsletter subscriber management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import SiteSetting, ContactMessage, Testimonial, FAQ, NewsletterSubscriber


class SiteSettingAdmin(admin.ModelAdmin):
    """Admin interface for Site Settings"""
    list_display = ('site_name', 'contact_email', 'contact_phone', 'updated_at')
    list_editable = ('contact_email', 'contact_phone')

    def has_add_permission(self, request):
        """Allow only one site settings instance"""
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of site settings"""
        return False


class ContactMessageAdmin(admin.ModelAdmin):
    """Admin interface for Contact Messages"""
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'ip_address', 'created_at')
    date_hierarchy = 'created_at'

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly for existing objects"""
        if obj:
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark selected messages as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')

    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        """Mark selected messages as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} message(s) marked as unread.')

    mark_as_unread.short_description = "Mark selected messages as unread"


class TestimonialAdmin(admin.ModelAdmin):
    """Admin interface for Testimonials"""
    list_display = ('client_name', 'client_location', 'client_type', 'rating', 'is_featured', 'created_at')
    list_filter = ('client_type', 'rating', 'is_featured', 'created_at')
    search_fields = ('client_name', 'client_location', 'content')
    list_editable = ('is_featured', 'rating')
    readonly_fields = ('created_at', 'display_client_photo')
    fieldsets = (
        ('Client Information', {
            'fields': ('client_name', 'client_location', 'client_type', 'client_photo', 'display_client_photo')
        }),
        ('Testimonial Content', {
            'fields': ('content', 'rating')
        }),
        ('Display Settings', {
            'fields': ('is_featured',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def display_client_photo(self, obj):
        """Display client photo in admin"""
        if obj.client_photo:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 50%; object-fit: cover;" />',
                obj.client_photo.url)
        return "No photo"

    display_client_photo.short_description = "Current Photo"


class FAQAdmin(admin.ModelAdmin):
    """Admin interface for FAQs"""
    list_display = ('question', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active', 'category')
    ordering = ('order', 'question')


class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin interface for Newsletter Subscribers"""
    list_display = ('email', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        """Activate selected subscribers"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriber(s) activated.')

    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        """Deactivate selected subscribers"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriber(s) deactivated.')

    deactivate_subscribers.short_description = "Deactivate selected subscribers"


# Register models with admin site
admin.site.register(SiteSetting, SiteSettingAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(Testimonial, TestimonialAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
