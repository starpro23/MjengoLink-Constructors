from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
"""
View Functions for Projects App
Contains views for:
- Project creation and management
- Bidding system
- Project browsing and search
- Messaging between users
- Milestone tracking
- Review system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (TemplateView, ListView, DetailView,
                                  CreateView, UpdateView, DeleteView, FormView, View)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Sum, Min, Max, Q, Count, Avg, F, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal

from .models import Project, ProjectImage, Bid, ProjectMessage, ProjectMilestone, ProjectReview
from .forms import (ProjectForm, ProjectImageForm, BidForm, MessageForm,
                    MilestoneForm, ReviewForm, ProjectSearchForm)
from users.models import ArtisanProfile, UserProfile


class ProjectListView(ListView):
    """
    List all active projects with filtering and search
    """
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        """Filter projects based on query parameters"""
        queryset = Project.objects.filter(
            status__in=['posted', 'bidding_closed', 'assigned', 'in_progress']
        ).select_related('homeowner', 'assigned_to')

        # Get filter parameters
        category = self.request.GET.get('category')
        location = self.request.GET.get('location')
        min_budget = self.request.GET.get('min_budget')
        max_budget = self.request.GET.get('max_budget')
        sort = self.request.GET.get('sort', 'newest')

        # Apply filters
        if category and category != 'all':
            queryset = queryset.filter(category=category)

        if location:
            queryset = queryset.filter(location__icontains=location)

        if min_budget:
            queryset = queryset.filter(budget_min__gte=min_budget)

        if max_budget:
            queryset = queryset.filter(budget_max__lte=max_budget)

        # Apply sorting
        if sort == 'newest':
            queryset = queryset.order_by('-posted_at')
        elif sort == 'oldest':
            queryset = queryset.order_by('posted_at')
        elif sort == 'budget_low':
            queryset = queryset.order_by('budget_min')
        elif sort == 'budget_high':
            queryset = queryset.order_by('-budget_max')
        elif sort == 'deadline':
            queryset = queryset.order_by('bidding_deadline')

        return queryset

    def your_view(request):
        context = {
            'rating_range': range(5),  # or range(1, 6) depending on your needs
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter form
        context['search_form'] = ProjectSearchForm(self.request.GET or None)

        # Add filter values for template
        context['current_category'] = self.request.GET.get('category', 'all')
        context['current_location'] = self.request.GET.get('location', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')

        # Add stats
        context['stats'] = {
            'total_projects': self.get_queryset().count(),
            'categories': Project.objects.values('category').annotate(
                count=Count('category')
            ).order_by('-count'),
        }

        return context


class ProjectDetailView(DetailView):
    """
    View project details
    """
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Increment view count
        if not self.request.user.is_authenticated or self.request.user != self.object.homeowner:
            self.object.view_count += 1
            self.object.save(update_fields=['view_count'])

        # Get project images
        context['images'] = self.object.images.all()

        # Get bids for this project
        if self.request.user.is_authenticated:
            if self.request.user == self.object.homeowner or self.request.user.is_staff:
                # Show all bids to homeowner
                context['bids'] = self.object.bids.select_related('artisan').all()
            elif self.request.user.profile.user_type == 'artisan':
                # Show artisan's own bid if they placed one
                context['user_bid'] = self.object.bids.filter(artisan=self.request.user).first()

        # Get milestones
        context['milestones'] = self.object.milestones.all()

        # Get messages if user is involved
        if self.request.user.is_authenticated:
            if self.request.user == self.object.homeowner or self.request.user == self.object.assigned_to:
                context['messages'] = self.object.messages.filter(
                    Q(sender=self.request.user) | Q(receiver=self.request.user)
                ).select_related('sender', 'receiver').order_by('created_at')[:50]

        # Check if user can bid
        if self.request.user.is_authenticated:
            context['can_bid'] = (
                    self.request.user.profile.user_type == 'artisan' and
                    self.object.status == 'posted' and
                    not self.object.bids.filter(artisan=self.request.user).exists()
            )

        # Check if user can message
        context['can_message'] = (
                self.request.user.is_authenticated and
                self.request.user != self.object.homeowner and
                self.object.assigned_to is None
        )

        # Add review if project is completed
        if self.object.status == 'completed' and self.request.user.is_authenticated:
            context['user_review'] = ProjectReview.objects.filter(
                project=self.object,
                reviewer=self.request.user
            ).first()

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new project
    """
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'
    success_url = reverse_lazy('projects:my_projects')

    def form_valid(self, form):
        """Set homeowner and initial status"""
        project = form.save(commit=False)
        project.homeowner = self.request.user
        project.status = 'draft'
        project.save()

        # Handle image uploads
        images = self.request.FILES.getlist('images')
        for i, image in enumerate(images[:5]):  # Limit to 5 images
            ProjectImage.objects.create(
                project=project,
                image=image,
                is_primary=(i == 0)
            )

        messages.success(self.request, 'Project created successfully!')

        # Redirect to publish or save as draft
        if 'publish' in self.request.POST:
            project.status = 'posted'
            project.posted_at = timezone.now()
            project.save()
            messages.success(self.request, 'Project published!')
            return redirect('projects:detail', pk=project.pk)
        else:
            messages.info(self.request, 'Project saved as draft. You can publish it later.')
            return redirect('projects:my_projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['image_form'] = ProjectImageForm()
        return context


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing project
    """
    model = Project
    form_class = ProjectForm
    template_name = 'projects/update.html'

    def test_func(self):
        """Check if user can edit this project"""
        project = self.get_object()
        return self.request.user == project.homeowner and project.status in ['draft', 'posted']

    def form_valid(self, form):
        """Update project"""
        project = form.save()

        # Handle image uploads
        images = self.request.FILES.getlist('images')
        for i, image in enumerate(images[:5]):
            ProjectImage.objects.create(
                project=project,
                image=image,
                is_primary=False
            )

        # Handle primary image selection
        primary_image_id = self.request.POST.get('primary_image')
        if primary_image_id:
            project.images.all().update(is_primary=False)
            project.images.filter(id=primary_image_id).update(is_primary=True)

        messages.success(self.request, 'Project updated successfully!')

        if 'publish' in self.request.POST and project.status == 'draft':
            project.status = 'posted'
            project.posted_at = timezone.now()
            project.save()
            messages.success(self.request, 'Project published!')

        return redirect('projects:detail', pk=project.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all()
        context['image_form'] = ProjectImageForm()
        return context


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete a project
    """
    model = Project
    template_name = 'projects/delete.html'
    success_url = reverse_lazy('projects:my_projects')

    def test_func(self):
        """Check if user can delete this project"""
        project = self.get_object()
        return self.request.user == project.homeowner and project.status in ['draft', 'posted']

    def delete(self, request, *args, **kwargs):
        """Set project status to cancelled instead of deleting"""
        project = self.get_object()
        project.status = 'cancelled'
        project.save()
        messages.success(request, 'Project cancelled successfully.')
        return redirect(self.success_url)


class MyProjectsView(LoginRequiredMixin, ListView):
    """
    View user's own projects
    """
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        """Get projects for current user"""
        user = self.request.user

        if user.profile.user_type == 'homeowner':
            # Homeowner sees their own projects
            return Project.objects.filter(homeowner=user).order_by('-posted_at')
        else:
            # Artisan sees projects they're assigned to
            return Project.objects.filter(assigned_to=user).order_by('-assigned_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add project counts by status
        user = self.request.user
        queryset = self.get_queryset()

        context['stats'] = {
            'total': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'posted': queryset.filter(status='posted').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'completed': queryset.filter(status='completed').count(),
        }

        return context


class BrowseProjectsView(ListView):
    """
    Browse projects with advanced filtering
    """
    model = Project
    template_name = 'projects/browse.html'
    context_object_name = 'projects'
    paginate_by = 15

    def get_queryset(self):
        """Filter projects for browsing"""
        queryset = Project.objects.filter(status='posted').select_related('homeowner')

        # Apply filters from GET parameters
        filters = Q()

        # Category filter
        category = self.request.GET.get('category')
        if category and category != 'all':
            filters &= Q(category=category)

        # Location filter
        location = self.request.GET.get('location')
        if location:
            filters &= Q(location__icontains=location)

        # Budget range filter
        min_budget = self.request.GET.get('min_budget')
        max_budget = self.request.GET.get('max_budget')

        if min_budget:
            try:
                filters &= Q(budget_min__gte=Decimal(min_budget))
            except:
                pass

        if max_budget:
            try:
                filters &= Q(budget_max__lte=Decimal(max_budget))
            except:
                pass

        # Urgency filter
        urgency = self.request.GET.get('urgency')
        if urgency and urgency != 'all':
            filters &= Q(urgency=urgency)

        # Timeline filter
        timeline = self.request.GET.get('timeline')
        if timeline:
            if timeline == 'short':
                filters &= Q(preferred_timeline__icontains='week') | Q(preferred_timeline__icontains='days')
            elif timeline == 'medium':
                filters &= Q(preferred_timeline__icontains='month') | Q(preferred_timeline__icontains='weeks')
            elif timeline == 'long':
                filters &= Q(preferred_timeline__icontains='months') | Q(preferred_timeline__icontains='year')

        # Apply all filters
        queryset = queryset.filter(filters)

        # Apply sorting
        sort_by = self.request.GET.get('sort_by', 'newest')
        if sort_by == 'newest':
            queryset = queryset.order_by('-posted_at')
        elif sort_by == 'budget_low':
            queryset = queryset.order_by('budget_min')
        elif sort_by == 'budget_high':
            queryset = queryset.order_by('-budget_max')
        elif sort_by == 'deadline':
            queryset = queryset.order_by('bidding_deadline')
        elif sort_by == 'urgency':
            urgency_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
            queryset = sorted(queryset, key=lambda p: urgency_order.get(p.urgency, 4))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all unique locations for filter dropdown
        context['locations'] = Project.objects.filter(status='posted').values_list(
            'location', flat=True
        ).distinct().order_by('location')

        # Get category counts for filter
        context['category_counts'] = Project.objects.filter(status='posted').values(
            'category'
        ).annotate(count=Count('category')).order_by('-count')

        # Get current filter values
        context['current_filters'] = {
            'category': self.request.GET.get('category', 'all'),
            'location': self.request.GET.get('location', ''),
            'min_budget': self.request.GET.get('min_budget', ''),
            'max_budget': self.request.GET.get('max_budget', ''),
            'urgency': self.request.GET.get('urgency', 'all'),
            'timeline': self.request.GET.get('timeline', ''),
            'sort_by': self.request.GET.get('sort_by', 'newest'),
        }

        # Add recommended projects for artisans
        if self.request.user.is_authenticated and self.request.user.profile.user_type == 'artisan':
            try:
                artisan_profile = ArtisanProfile.objects.get(user=self.request.user)
                # Recommend projects in same category
                recommended = Project.objects.filter(
                    status='posted',
                    category=artisan_profile.trade
                ).exclude(
                    bids__artisan=self.request.user
                )[:5]
                context['recommended_projects'] = recommended
            except ArtisanProfile.DoesNotExist:
                pass

        return context


class BidCreateView(LoginRequiredMixin, CreateView):
    """
    Create a bid for a project
    """
    model = Bid
    form_class = BidForm
    template_name = 'projects/bid_create.html'

    def dispatch(self, request, *args, **kwargs):
        """Get project from URL and check permissions"""
        self.project = get_object_or_404(Project, id=kwargs['project_id'])

        # Check if user can bid on this project
        if not self.can_bid():
            messages.error(request, 'You cannot bid on this project.')
            return redirect('projects:detail', pk=self.project.id)

        return super().dispatch(request, *args, **kwargs)

    def can_bid(self):
        """Check if user can bid on this project"""
        user = self.request.user

        # User must be an artisan
        if user.profile.user_type != 'artisan':
            return False

        # Project must be open for bidding
        if self.project.status != 'posted':
            return False

        # User must not have already bid
        if self.project.bids.filter(artisan=user).exists():
            return False

        # User must be verified if project requires it
        if self.project.requires_verification:
            try:
                artisan_profile = ArtisanProfile.objects.get(user=user)
                if not artisan_profile.is_verified:
                    return False
            except ArtisanProfile.DoesNotExist:
                return False

        return True

    def form_valid(self, form):
        """Save bid with project and artisan"""
        bid = form.save(commit=False)
        bid.project = self.project
        bid.artisan = self.request.user

        # Check if bid is within budget range
        if bid.amount < self.project.budget_min:
            messages.warning(self.request,
                             f'Your bid is below the minimum budget (KES {self.project.budget_min:,.0f}). '
                             'The homeowner may consider more competitive bids.'
                             )

        if bid.amount > self.project.budget_max:
            messages.warning(self.request,
                             f'Your bid exceeds the maximum budget (KES {self.project.budget_max:,.0f}). '
                             'Consider adjusting your bid to stay within budget.'
                             )

        bid.save()

        # Update bid count on project
        self.project.bid_count += 1
        self.project.save(update_fields=['bid_count'])

        messages.success(self.request, 'Bid submitted successfully!')
        return redirect('projects:detail', pk=self.project.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['artisan_profile'] = ArtisanProfile.objects.filter(
            user=self.request.user
        ).first()
        return context


class BidListView(LoginRequiredMixin, ListView):
    """
    View bids for a project (homeowner only)
    """
    model = Bid
    template_name = 'projects/bid_list.html'
    context_object_name = 'bids'

    def get_queryset(self):
        """Get bids for specific project"""
        self.project = get_object_or_404(Project, id=self.kwargs['project_id'])

        # Check permission
        if self.request.user != self.project.homeowner and not self.request.user.is_staff:
            return Bid.objects.none()

        return Bid.objects.filter(
            project=self.project
        ).select_related('artisan', 'artisan__artisanprofile').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        # Get artisan stats for comparison
        bids_with_stats = []
        for bid in context['bids']:
            try:
                artisan_profile = bid.artisan.artisanprofile
                stats = {
                    'rating': artisan_profile.rating,
                    'completed_projects': artisan_profile.completed_projects,
                    'response_rate': artisan_profile.response_rate,
                    'avg_bid_acceptance': artisan_profile.avg_bid_acceptance,
                }
                bids_with_stats.append((bid, stats))
            except ArtisanProfile.DoesNotExist:
                bids_with_stats.append((bid, {}))

        context['bids_with_stats'] = bids_with_stats

        return context


class BidDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View bid details
    """
    model = Bid
    template_name = 'projects/bid_detail.html'
    context_object_name = 'bid'

    def test_func(self):
        """Check if user can view this bid"""
        bid = self.get_object()
        user = self.request.user

        return (
                user == bid.project.homeowner or
                user == bid.artisan or
                user.is_staff
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project

        # Get artisan profile and stats
        try:
            context['artisan_profile'] = self.object.artisan.artisanprofile
            context['artisan_reviews'] = ProjectReview.objects.filter(
                project__assigned_to=self.object.artisan
            )[:5]
        except ArtisanProfile.DoesNotExist:
            context['artisan_profile'] = None

        return context


class BidAcceptView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Accept a bid and assign project to artisan
    """

    def test_func(self):
        """Check if user can accept bid"""
        self.bid = get_object_or_404(Bid, id=self.kwargs['pk'])
        return self.request.user == self.bid.project.homeowner

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        bid = self.bid
        project = bid.project

        # Check if project is still open for bidding
        if project.status != 'posted':
            messages.error(request, 'This project is no longer open for bidding.')
            return redirect('projects:bid_list', project_id=project.id)

        # Update project
        project.assigned_to = bid.artisan
        project.assigned_at = timezone.now()
        project.status = 'assigned'
        project.final_budget = bid.amount
        project.save()

        # Update bid status
        bid.status = 'accepted'
        bid.accepted_at = timezone.now()
        bid.save()

        # Reject all other bids
        other_bids = project.bids.exclude(id=bid.id)
        other_bids.update(status='rejected', rejected_at=timezone.now())

        # Send notifications (you'll need to implement notification system)
        # send_bid_accepted_notification(bid)
        # send_project_assigned_notification(project)

        messages.success(request, f'Bid accepted! Project assigned to {bid.artisan.get_full_name()}.')
        return redirect('projects:detail', pk=project.id)


class BidRejectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Reject a bid
    """

    def test_func(self):
        """Check if user can reject bid"""
        self.bid = get_object_or_404(Bid, id=self.kwargs['pk'])
        return self.request.user == self.bid.project.homeowner

    def post(self, request, *args, **kwargs):
        bid = get_object_or_404(Bid, id=self.kwargs['pk'])

        # Check if bid can be rejected
        if bid.status != 'pending':
            messages.error(request, 'This bid cannot be rejected.')
            return redirect('projects:bid_list', project_id=bid.project.id)

        # Update bid
        bid.status = 'rejected'
        bid.rejected_at = timezone.now()
        bid.save()

        messages.success(request, 'Bid rejected.')
        return redirect('projects:bid_list', project_id=bid.project.id)


class BidWithdrawView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Withdraw a bid (artisan only)
    """

    def test_func(self):
        """Check if user can withdraw bid"""
        self.bid = get_object_or_404(Bid, id=self.kwargs['pk'])
        return self.request.user == self.bid.artisan

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        bid = self.bid
        project = bid.project

        # Check if bid can be withdrawn
        if bid.status != 'pending':
            messages.error(request, 'This bid cannot be withdrawn.')
            return redirect('projects:detail', pk=project.id)

        # Update bid
        bid.status = 'withdrawn'
        bid.withdrawn_at = timezone.now()
        bid.save()

        # Update project bid count
        project.bid_count -= 1
        project.save(update_fields=['bid_count'])

        messages.success(request, 'Bid withdrawn successfully.')
        return redirect('projects:detail', pk=project.id)


class MyBidsView(LoginRequiredMixin, ListView):
    """
    View artisan's bids
    """
    model = Bid
    template_name = 'projects/my_bids.html'
    context_object_name = 'bids'
    paginate_by = 10

    def get_queryset(self):
        """Get bids for current artisan"""
        return Bid.objects.filter(
            artisan=self.request.user
        ).select_related('project', 'project__homeowner').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get bid stats
        queryset = self.get_queryset()

        context['stats'] = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'accepted': queryset.filter(status='accepted').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'withdrawn': queryset.filter(status='withdrawn').count(),
        }

        return context


class MessageCreateView(LoginRequiredMixin, CreateView):
    """
    Send a message to project homeowner/artisan
    """
    model = ProjectMessage
    form_class = MessageForm
    template_name = 'projects/message_create.html'

    def dispatch(self, request, *args, **kwargs):
        """Get project and recipient"""
        self.project = get_object_or_404(Project, id=kwargs['project_id'])

        # Determine recipient
        if self.request.user == self.project.homeowner:
            # Homeowner can only message assigned artisan
            if self.project.assigned_to:
                self.recipient = self.project.assigned_to
            else:
                messages.error(request, 'No artisan assigned to this project yet.')
                return redirect('projects:detail', pk=self.project.id)
        else:
            # Artisan can message homeowner
            self.recipient = self.project.homeowner

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Save message with sender and recipient"""
        message = form.save(commit=False)
        message.project = self.project
        message.sender = self.request.user
        message.receiver = self.recipient
        message.save()

        messages.success(self.request, 'Message sent successfully!')
        return redirect('projects:conversation', project_id=self.project.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['recipient'] = self.recipient

        # Get conversation history
        context['conversation'] = ProjectMessage.objects.filter(
            project=self.project,
            sender__in=[self.request.user, self.recipient],
            receiver__in=[self.request.user, self.recipient]
        ).select_related('sender', 'receiver').order_by('created_at')[:50]

        return context


class ConversationView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View conversation for a project
    """
    model = ProjectMessage
    template_name = 'projects/conversation.html'
    context_object_name = 'messages'

    def test_func(self):
        """Check if user can view conversation"""
        self.project = get_object_or_404(Project, id=self.kwargs['project_id'])
        return (
                self.request.user == self.project.homeowner or
                self.request.user == self.project.assigned_to or
                self.request.user.is_staff
        )

    def get_queryset(self):
        """Get messages for this project"""
        return ProjectMessage.objects.filter(
            project=self.project
        ).select_related('sender', 'receiver').order_by('created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        # Determine other participant
        if self.request.user == self.project.homeowner:
            context['other_participant'] = self.project.assigned_to
        else:
            context['other_participant'] = self.project.homeowner

        # Mark unread messages as read
        unread_messages = context['messages'].filter(
            receiver=self.request.user,
            is_read=False
        )
        unread_messages.update(is_read=True, read_at=timezone.now())

        # Add message form
        context['message_form'] = MessageForm()

        return context


class MilestoneCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a milestone for a project
    """
    model = ProjectMilestone
    form_class = MilestoneForm
    template_name = 'projects/milestone_create.html'

    def test_func(self):
        """Check if user can create milestone"""
        self.project = get_object_or_404(Project, id=self.kwargs['project_id'])
        return (
                self.request.user == self.project.homeowner or
                self.request.user == self.project.assigned_to
        )

    def form_valid(self, form):
        """Save milestone with project"""
        milestone = form.save(commit=False)
        milestone.project = self.project
        milestone.save()

        messages.success(self.request, 'Milestone created successfully!')
        return redirect('projects:detail', pk=self.project.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


class MilestoneUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update a milestone
    """
    model = ProjectMilestone
    form_class = MilestoneForm
    template_name = 'projects/milestone_update.html'

    def test_func(self):
        """Check if user can update milestone"""
        milestone = self.get_object()
        project = milestone.project
        return (
                self.request.user == project.homeowner or
                self.request.user == project.assigned_to
        )

    def form_valid(self, form):
        """Update milestone"""
        milestone = form.save()

        # Update project status if milestone is completed
        if milestone.status == 'completed':
            project = milestone.project
            completed_milestones = project.milestones.filter(status='completed').count()
            total_milestones = project.milestones.count()

            # Check if all milestones are completed
            if completed_milestones == total_milestones:
                project.status = 'completed'
                project.completed_at = timezone.now()
                project.save()

        messages.success(self.request, 'Milestone updated successfully!')
        return redirect('projects:detail', pk=milestone.project.id)


class ReviewCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a review for a completed project
    """
    model = ProjectReview
    form_class = ReviewForm
    template_name = 'projects/review_create.html'

    def test_func(self):
        """Check if user can review project"""
        self.project = get_object_or_404(Project, id=self.kwargs['project_id'])

        # Check if project is completed
        if self.project.status != 'completed':
            return False

        # Check if user is homeowner or artisan involved
        if self.request.user == self.project.homeowner:
            self.review_type = 'homeowner'
            self.reviewee = self.project.assigned_to
        elif self.request.user == self.project.assigned_to:
            self.review_type = 'artisan'
            self.reviewee = self.project.homeowner
        else:
            return False

        # Check if review already exists
        if ProjectReview.objects.filter(
                project=self.project,
                reviewer=self.request.user,
                review_type=self.review_type
        ).exists():
            return False

        return True

    def form_valid(self, form):
        """Save review"""
        review = form.save(commit=False)
        review.project = self.project
        review.reviewer = self.request.user
        review.reviewee = self.reviewee
        review.review_type = self.review_type
        review.save()

        # Update artisan stats if applicable
        if self.review_type == 'homeowner' and self.reviewee:
            try:
                artisan_profile = ArtisanProfile.objects.get(user=self.reviewee)
                artisan_profile.update_rating()
                artisan_profile.save()
            except ArtisanProfile.DoesNotExist:
                pass

        messages.success(self.request, 'Review submitted successfully!')
        return redirect('projects:detail', pk=self.project.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['reviewee'] = self.reviewee
        context['review_type'] = self.review_type
        return context


class ProjectSearchView(ListView):
    """
    Search projects with full-text search
    """
    model = Project
    template_name = 'projects/search.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        """Search projects based on query"""
        query = self.request.GET.get('q', '').strip()

        if not query:
            return Project.objects.none()

        # Build search query
        search_query = Q()

        # Search in title and description
        search_query |= Q(title__icontains=query)
        search_query |= Q(description__icontains=query)
        search_query |= Q(location__icontains=query)
        search_query |= Q(category__icontains=query)
        search_query |= Q(specific_requirements__icontains=query)

        # Filter only posted projects
        queryset = Project.objects.filter(
            search_query,
            status='posted'
        ).select_related('homeowner')

        return queryset.order_by('-posted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['total_results'] = self.get_queryset().count()
        return context


class ProjectDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for project statistics and overview
    """
    template_name = 'projects/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.profile.user_type == 'homeowner':
            # Homeowner dashboard
            projects = Project.objects.filter(homeowner=user)

            context['stats'] = {
                'total_projects': projects.count(),
                'active_projects': projects.filter(status__in=['posted', 'assigned', 'in_progress']).count(),
                'completed_projects': projects.filter(status='completed').count(),
                'total_spent': projects.filter(status='completed').aggregate(
                    total=Sum('final_price')
                )['total'] or 0,
                'avg_bid_count': projects.filter(bid_count__gt=0).aggregate(
                    avg=Avg('bid_count')
                )['avg'] or 0,
            }

            # Recent projects
            context['recent_projects'] = projects.order_by('-posted_at')[:5]

            # Projects by status
            context['projects_by_status'] = projects.values('status').annotate(
                count=Count('id')
            ).order_by('-count')

        else:
            # Artisan dashboard
            bids = Bid.objects.filter(artisan=user)
            projects = Project.objects.filter(assigned_to=user)

            context['stats'] = {
                'total_bids': bids.count(),
                'accepted_bids': bids.filter(status='accepted').count(),
                'active_projects': projects.filter(status__in=['assigned', 'in_progress']).count(),
                'completed_projects': projects.filter(status='completed').count(),
                'total_earnings': projects.filter(status='completed').aggregate(
                    total=Sum('final_budget')
                )['total'] or 0,
                'acceptance_rate': (
                            bids.filter(status='accepted').count() / bids.count() * 100) if bids.count() > 0 else 0,
            }

            # Recent bids
            context['recent_bids'] = bids.select_related('project').order_by('-created_at')[:5]

            # Recent projects
            context['recent_projects'] = projects.order_by('-assigned_at')[:5]

        return context


@method_decorator(csrf_exempt, name='dispatch')
class ProjectImageView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Handle project image uploads and deletions
    """

    def test_func(self):
        """Check if user can manage project images"""
        self.project = get_object_or_404(Project, id=self.kwargs['project_id'])
        return self.request.user == self.project.homeowner

    def post(self, request, *args, **kwargs):
        """Upload new image"""
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)

        image = request.FILES['image']

        # Check file size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File size too large. Max 5MB.'}, status=400)

        # Create image
        project_image = ProjectImage.objects.create(
            project=self.project,
            image=image,
            is_primary=False
        )

        return JsonResponse({
            'success': True,
            'image_id': project_image.id,
            'image_url': project_image.image.url
        })

    def delete(self, request, *args, **kwargs):
        """Delete image"""
        image_id = request.GET.get('image_id')
        if not image_id:
            return JsonResponse({'error': 'Image ID required'}, status=400)

        try:
            image = ProjectImage.objects.get(id=image_id, project=self.project)

            # Don't delete if it's the only image
            if self.project.images.count() <= 1:
                return JsonResponse({'error': 'Cannot delete the only image'}, status=400)

            # Delete the image
            image.delete()
            return JsonResponse({'success': True})
        except ProjectImage.DoesNotExist:
            return JsonResponse({'error': 'Image not found'}, status=404)


class ProjectStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Update project status
    """

    def test_func(self):
        """Check if user can update project status"""
        self.project = get_object_or_404(Project, id=self.kwargs['project_id'])

        if self.request.user == self.project.homeowner:
            # Homeowner can update from draft to posted
            return self.project.status == 'draft'
        elif self.request.user == self.project.assigned_to:
            # Artisan can update from assigned to in_progress
            return self.project.status == 'assigned'
        else:
            return False

    def post(self, request, *args, **kwargs):
        project = self.project

        if request.user == project.homeowner:
            # Homeowner publishing project
            project.status = 'posted'
            project.posted_at = timezone.now()
            project.save()
            messages.success(request, 'Project published successfully!')

        elif request.user == project.assigned_to:
            # Artisan starting work
            project.status = 'in_progress'
            project.started_at = timezone.now()
            project.save()
            messages.success(request, 'Project marked as in progress!')

        return redirect('projects:detail', pk=project.id)


# AJAX Views for dynamic updates

@login_required
@require_GET
def get_bid_stats(request, project_id):
    """Get bid statistics for a project"""
    project = get_object_or_404(Project, id=project_id)

    if request.user != project.homeowner and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    bids = project.bids.all()

    stats = {
        'total_bids': bids.count(),
        'avg_bid': bids.aggregate(avg=Avg('amount'))['avg'] or 0,
        'min_bid': bids.aggregate(min=Min('amount'))['min'] or 0,
        'max_bid': bids.aggregate(max=Max('amount'))['max'] or 0,
        'pending_bids': bids.filter(status='pending').count(),
    }

    return JsonResponse(stats)


@login_required
@require_POST
def mark_message_read(request, message_id):
    """Mark a message as read"""
    message = get_object_or_404(ProjectMessage, id=message_id, receiver=request.user)

    if not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()

    return JsonResponse({'success': True})


@login_required
@require_GET
def get_unread_message_count(request):
    """Get count of unread messages"""
    count = ProjectMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return JsonResponse({'count': count})


# Error handling views

def handler404(request, exception):
    """Custom 404 handler for projects"""
    return render(request, 'projects/404.html', status=404)


def handler500(request):
    """Custom 500 handler for projects"""
    return render(request, 'projects/500.html', status=500)


def handler403(request, exception):
    """Custom 403 handler for projects"""
    return render(request, 'projects/403.html', status=403)


def handler400(request, exception):
    """Custom 400 handler for projects"""
    return render(request, 'projects/400.html', status=400)
