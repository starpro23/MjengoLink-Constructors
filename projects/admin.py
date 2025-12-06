"""
Django Admin Configuration for Projects App
Contains admin interfaces for:
- Project management and moderation
- Bid review and approval
- Message monitoring
- Milestone tracking
- Review and rating management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Project, ProjectImage, Bid, ProjectMessage, ProjectMilestone, ProjectReview


class ProjectImageInline(admin.TabularInline):
    """Inline admin for project images"""
    model = ProjectImage
    extra = 0
    fields = ('image', 'caption', 'is_primary', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class ProjectMilestoneInline(admin.TabularInline):
    """Inline admin for project milestones"""
    model = ProjectMilestone
    extra = 0
    fields = ('title', 'amount', 'due_date', 'status', 'completed_at')
    readonly_fields = ('completed_at',)


class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Projects"""
    list_display = ('title', 'homeowner_info', 'category_badge', 'budget_range',
                    'location_short', 'status_badge', 'posted_at', 'bid_count')
    list_filter = ('status', 'category', 'urgency', 'posted_at', 'location')
    search_fields = ('title', 'description', 'homeowner__username', 'homeowner__email', 'location')
    readonly_fields = ('posted_at', 'updated_at', 'assigned_at', 'started_at',
                       'completed_at', 'view_count', 'bid_count', 'homeowner_info',
                       'assigned_to_info', 'project_images')
    inlines = [ProjectImageInline, ProjectMilestoneInline]
    list_per_page = 50

    fieldsets = (
        ('Project Details', {
            'fields': ('title', 'description', 'homeowner_info', 'category', 'status')
        }),
        ('Location & Budget', {
            'fields': ('location', 'exact_address', 'budget_min', 'budget_max', 'budget_range')
        }),
        ('Timeline & Requirements', {
            'fields': ('preferred_timeline', 'urgency', 'area_size',
                       'materials_provided', 'special_requirements')
        }),
        ('Assignment', {
            'fields': ('assigned_to_info', 'final_price', 'final_timeline'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('posted_at', 'bidding_deadline', 'assigned_at',
                       'started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'bid_count'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('project_images',),
            'classes': ('collapse',)
        }),
    )

    def homeowner_info(self, obj):
        """Display homeowner information"""
        if obj.homeowner:
            url = reverse('admin:auth_user_change', args=[obj.homeowner.id])
            return format_html('<a href="{}">{}</a>', url, obj.homeowner.get_full_name())
        return '-'

    homeowner_info.short_description = 'Homeowner'

    def assigned_to_info(self, obj):
        """Display assigned artisan information"""
        if obj.assigned_to:
            url = reverse('admin:auth_user_change', args=[obj.assigned_to.id])
            return format_html('<a href="{}">{}</a>', url, obj.assigned_to.get_full_name())
        return '-'

    assigned_to_info.short_description = 'Assigned To'

    def budget_range(self, obj):
        """Display budget range"""
        return f"KES {obj.budget_min:,.0f} - KES {obj.budget_max:,.0f}"

    budget_range.short_description = 'Budget Range'

    def location_short(self, obj):
        """Display shortened location"""
        if len(obj.location) > 30:
            return f"{obj.location[:30]}..."
        return obj.location

    location_short.short_description = 'Location'

    def category_badge(self, obj):
        """Display category as badge"""
        return format_html(
            '<span class="badge bg-info">{}</span>',
            obj.get_category_display()
        )

    category_badge.short_description = 'Category'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'draft': 'secondary',
            'posted': 'primary',
            'bidding_closed': 'warning',
            'assigned': 'info',
            'in_progress': 'success',
            'on_hold': 'dark',
            'completed': 'success',
            'cancelled': 'danger',
            'disputed': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def project_images(self, obj):
        """Display project images"""
        images = obj.images.all()
        if images:
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in images[:5]:  # Show max 5 images
                if img.image:
                    html += f'<img src="{img.image.url}" width="100" height="100" style="object-fit: cover; border-radius: 5px;">'
            html += '</div>'
            return format_html(html)
        return 'No images'

    project_images.short_description = 'Images'

    actions = ['approve_projects', 'close_bidding', 'mark_as_completed', 'cancel_projects']

    def approve_projects(self, request, queryset):
        """Approve selected projects"""
        updated = queryset.update(status='posted')
        self.message_user(request, f'{updated} project(s) approved and posted.')

    approve_projects.short_description = "Approve and post projects"

    def close_bidding(self, request, queryset):
        """Close bidding for selected projects"""
        updated = queryset.update(status='bidding_closed')
        self.message_user(request, f'{updated} project(s) bidding closed.')

    close_bidding.short_description = "Close bidding"

    def mark_as_completed(self, request, queryset):
        """Mark selected projects as completed"""
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} project(s) marked as completed.')

    mark_as_completed.short_description = "Mark as completed"


class BidAdmin(admin.ModelAdmin):
    """Admin interface for Bids"""
    list_display = ('project_title', 'artisan_info', 'amount_formatted',
                    'timeline', 'status_badge', 'submitted_at')
    list_filter = ('status', 'submitted_at', 'project__category')
    search_fields = ('project__title', 'artisan__username', 'proposal')
    readonly_fields = ('submitted_at', 'updated_at', 'accepted_at',
                       'project_link', 'artisan_info')

    fieldsets = (
        ('Bid Details', {
            'fields': ('project_link', 'artisan_info', 'status')
        }),
        ('Proposal', {
            'fields': ('amount', 'timeline', 'proposal', 'notes')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )

    def project_title(self, obj):
        """Display project title"""
        return obj.project.title

    project_title.short_description = 'Project'

    def artisan_info(self, obj):
        """Display artisan information"""
        if obj.artisan:
            url = reverse('admin:auth_user_change', args=[obj.artisan.id])
            return format_html('<a href="{}">{}</a>', url, obj.artisan.get_full_name())
        return '-'

    artisan_info.short_description = 'Artisan'

    def project_link(self, obj):
        """Display project link"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.title)

    project_link.short_description = 'Project'

    def amount_formatted(self, obj):
        """Format amount"""
        return f"KES {obj.amount:,.2f}"

    amount_formatted.short_description = 'Amount'

    def status_badge(self, obj):
        """Display status as badge"""
        colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'withdrawn': 'secondary',
            'expired': 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    actions = ['accept_bids', 'reject_bids', 'mark_as_withdrawn']

    def accept_bids(self, request, queryset):
        """Accept selected bids"""
        updated = queryset.update(status='accepted')
        self.message_user(request, f'{updated} bid(s) accepted.')

    accept_bids.short_description = "Accept bids"

    def reject_bids(self, request, queryset):
        """Reject selected bids"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} bid(s) rejected.')

    reject_bids.short_description = "Reject bids"


class ProjectMessageAdmin(admin.ModelAdmin):
    """Admin interface for Project Messages"""
    list_display = ('project_title', 'sender_info', 'receiver_info',
                    'message_preview', 'is_read_badge', 'created_at')
    list_filter = ('is_read', 'created_at', 'project')
    search_fields = ('message', 'sender__username', 'receiver__username', 'project__title')
    readonly_fields = ('created_at', 'project_link', 'sender_info', 'receiver_info')

    fieldsets = (
        ('Message Details', {
            'fields': ('project_link', 'sender_info', 'receiver_info', 'is_read')
        }),
        ('Message Content', {
            'fields': ('message',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def project_title(self, obj):
        """Display project title"""
        return obj.project.title

    project_title.short_description = 'Project'

    def sender_info(self, obj):
        """Display sender information"""
        if obj.sender:
            url = reverse('admin:auth_user_change', args=[obj.sender.id])
            return format_html('<a href="{}">{}</a>', url, obj.sender.get_full_name())
        return '-'

    sender_info.short_description = 'Sender'

    def receiver_info(self, obj):
        """Display receiver information"""
        if obj.receiver:
            url = reverse('admin:auth_user_change', args=[obj.receiver.id])
            return format_html('<a href="{}">{}</a>', url, obj.receiver.get_full_name())
        return '-'

    receiver_info.short_description = 'Receiver'

    def project_link(self, obj):
        """Display project link"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.title)

    project_link.short_description = 'Project'

    def message_preview(self, obj):
        """Display message preview"""
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message

    message_preview.short_description = 'Message'

    def is_read_badge(self, obj):
        """Display read status as badge"""
        if obj.is_read:
            return format_html('<span class="badge bg-success">Read</span>')
        return format_html('<span class="badge bg-warning">Unread</span>')

    is_read_badge.short_description = 'Read Status'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark selected messages as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')

    mark_as_read.short_description = "Mark as read"


class ProjectMilestoneAdmin(admin.ModelAdmin):
    """Admin interface for Project Milestones"""
    list_display = ('title', 'project_title', 'amount_formatted',
                    'due_date', 'status_badge', 'completed_at')
    list_filter = ('status', 'due_date', 'project')
    search_fields = ('title', 'description', 'project__title')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'approved_at', 'project_link')

    fieldsets = (
        ('Milestone Details', {
            'fields': ('project_link', 'title', 'description', 'status')
        }),
        ('Financial Details', {
            'fields': ('amount', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('completed_at', 'approved_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def project_title(self, obj):
        """Display project title"""
        return obj.project.title

    project_title.short_description = 'Project'

    def project_link(self, obj):
        """Display project link"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.title)

    project_link.short_description = 'Project'

    def amount_formatted(self, obj):
        """Format amount"""
        return f"KES {obj.amount:,.2f}"

    amount_formatted.short_description = 'Amount'

    def status_badge(self, obj):
        """Display status as badge"""
        colors = {
            'pending': 'secondary',
            'in_progress': 'info',
            'completed': 'warning',
            'approved': 'success',
            'paid': 'primary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Status'


class ProjectReviewAdmin(admin.ModelAdmin):
    """Admin interface for Project Reviews"""
    list_display = ('project_title', 'reviewer_info', 'reviewee_info',
                    'rating_stars', 'is_verified_badge', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('title', 'content', 'reviewer__username', 'reviewee__username')
    readonly_fields = ('created_at', 'updated_at', 'project_link',
                       'reviewer_info', 'reviewee_info')

    fieldsets = (
        ('Review Details', {
            'fields': ('project_link', 'reviewer_info', 'reviewee_info',
                       'rating', 'is_verified')
        }),
        ('Review Content', {
            'fields': ('title', 'content')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def project_title(self, obj):
        """Display project title"""
        return obj.project.title

    project_title.short_description = 'Project'

    def reviewer_info(self, obj):
        """Display reviewer information"""
        if obj.reviewer:
            url = reverse('admin:auth_user_change', args=[obj.reviewer.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewer.get_full_name())
        return '-'

    reviewer_info.short_description = 'Reviewer'

    def reviewee_info(self, obj):
        """Display reviewee information"""
        if obj.reviewee:
            url = reverse('admin:auth_user_change', args=[obj.reviewee.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewee.get_full_name())
        return '-'

    reviewee_info.short_description = 'Reviewee'

    def project_link(self, obj):
        """Display project link"""
        url = reverse('admin:projects_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.title)

    project_link.short_description = 'Project'

    def rating_stars(self, obj):
        """Display rating as stars"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold; font-size: 1.2em;">{}</span>', stars)

    rating_stars.short_description = 'Rating'

    def is_verified_badge(self, obj):
        """Display verification status"""
        if obj.is_verified:
            return format_html('<span class="badge bg-success">Verified</span>')
        return format_html('<span class="badge bg-secondary">Unverified</span>')

    is_verified_badge.short_description = 'Verified'

    actions = ['verify_reviews', 'unverify_reviews']

    def verify_reviews(self, request, queryset):
        """Verify selected reviews"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} review(s) verified.')

    verify_reviews.short_description = "Verify reviews"


# Register models with admin site
admin.site.register(Project, ProjectAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(ProjectMessage, ProjectMessageAdmin)
admin.site.register(ProjectMilestone, ProjectMilestoneAdmin)
admin.site.register(ProjectReview, ProjectReviewAdmin)
