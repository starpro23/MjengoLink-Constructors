"""
View Functions for Core App
Contains views for:
- Public website pages
- Contact form handling
- Newsletter management
- SEO and sitemap generation
- Error page customization
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, FormView, CreateView
from django.views.generic.edit import FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse

from .models import SiteSetting, ContactMessage, Testimonial, FAQ, NewsletterSubscriber
from .forms import ContactForm, NewsletterForm
# from .sitemaps import StaticViewSitemap


class HomeView(TemplateView):
    """
    Homepage View
    Displays:
    - Hero section with stats
    - Featured testimonials
    - How it works
    - Trade categories
    - Call to action
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get site settings
        context['site_settings'] = SiteSetting.objects.first()

        # Get featured testimonials
        context['testimonials'] = Testimonial.objects.filter(is_featured=True)[:3]

        # Get FAQ categories for dropdown
        context['faq_categories'] = FAQ.objects.filter(is_active=True).values_list('category', flat=True).distinct()

        # Mock stats (in production, these would come from database)
        context['stats'] = {
            'verified_artisans': 2500,
            'projects_completed': 15000,
            'satisfaction_rate': 98,
            'support_availability': '24/7',
            'average_rating': 4.8,
        }

        # Trade categories for the grid
        context['trades'] = [
            {'name': 'Plumbers', 'icon': 'bi-droplet'},
            {'name': 'Electricians', 'icon': 'bi-lightning-charge'},
            {'name': 'Masons', 'icon': 'bi-bricks'},
            {'name': 'Carpenters', 'icon': 'bi-tools'},
            {'name': 'Painters', 'icon': 'bi-brush'},
            {'name': 'Welders', 'icon': 'bi-wrench'},
            {'name': 'Roofers', 'icon': 'bi-house-door'},
            {'name': 'Tilers', 'icon': 'bi-grid-3x3-gap'},
            {'name': 'Landscapers', 'icon': 'bi-tree'},
            {'name': 'Interior Designers', 'icon': 'bi-columns-gap'},
        ]

        return context


class AboutView(TemplateView):
    """About Us page"""
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        return context


class ServicesView(TemplateView):
    """Services page"""
    template_name = 'core/services.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()

        # All available trades for services page
        context['trades'] = [
            {'name': 'Plumbing', 'icon': 'bi-droplet',
             'description': 'Pipe installation, drainage systems, water heater installation'},
            {'name': 'Electrical', 'icon': 'bi-lightning-charge',
             'description': 'Wiring, lighting installation, electrical repairs'},
            {'name': 'Masonry', 'icon': 'bi-bricks', 'description': 'Brickwork, concrete work, foundation laying'},
            {'name': 'Carpentry', 'icon': 'bi-tools',
             'description': 'Furniture making, roofing, flooring installation'},
            {'name': 'Painting', 'icon': 'bi-brush', 'description': 'Interior/exterior painting, wall finishing'},
            {'name': 'Welding', 'icon': 'bi-wrench', 'description': 'Metal fabrication, gates, railings'},
            {'name': 'Roofing', 'icon': 'bi-house-door', 'description': 'Roof installation, repair, waterproofing'},
            {'name': 'Tiling', 'icon': 'bi-grid-3x3-gap', 'description': 'Floor tiling, wall tiling, pattern design'},
            {'name': 'Landscaping', 'icon': 'bi-tree', 'description': 'Garden design, lawn installation, irrigation'},
            {'name': 'Interior Design', 'icon': 'bi-columns-gap',
             'description': 'Space planning, color consultation, furniture selection'},
        ]

        return context


class HowItWorksView(TemplateView):
    """How It Works page"""
    template_name = 'core/how-it-works.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        return context


class ContactView(FormView):
    """Contact page with form"""
    template_name = 'core/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()

        # Get FAQs for contact page
        context['faqs'] = FAQ.objects.filter(is_active=True, category__in=['general', 'payments', 'safety'])[:5]

        return context

    def form_valid(self, form):
        """Process valid contact form"""
        # Save contact message
        contact_message = form.save(commit=False)
        contact_message.ip_address = self.request.META.get('REMOTE_ADDR')
        contact_message.save()

        # Send success message
        messages.success(self.request,
                         'Thank you for your message! We will get back to you within 24 hours.')

        # In production, email would be sent here via signals
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request,
                       'Please correct the errors below and try again.')
        return super().form_invalid(form)


class ContactSubmitView(CreateView):
    """API-style contact form submission (for AJAX)"""
    model = ContactMessage
    fields = ['name', 'email', 'phone', 'subject', 'message']

    def form_valid(self, form):
        """Process valid form submission"""
        contact_message = form.save(commit=False)
        contact_message.ip_address = self.request.META.get('REMOTE_ADDR')
        contact_message.save()

        # Return JSON response for AJAX calls
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your message! We will contact you soon.'
            })

        messages.success(self.request, 'Thank you for your message!')
        return redirect('contact')

    def form_invalid(self, form):
        """Handle invalid form submission"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

        messages.error(self.request, 'Please correct the errors below.')
        return redirect('contact')


class NewsletterSubscribeView(FormView):
    """Newsletter subscription"""
    form_class = NewsletterForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """Process newsletter subscription"""
        email = form.cleaned_data['email']

        # Check if already subscribed
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={'is_active': True}
        )

        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Thank you for subscribing to our newsletter!'
            })

        messages.success(self.request, 'Thank you for subscribing!')
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid subscription"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

        messages.error(self.request, 'Please enter a valid email address.')
        return redirect('home')


class NewsletterUnsubscribeView(TemplateView):
    """Newsletter unsubscribe"""
    template_name = 'core/newsletter_unsubscribe.html'

    def get(self, request, *args, **kwargs):
        """Handle unsubscribe request"""
        email = kwargs.get('email')

        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            subscriber.is_active = False
            subscriber.save()
            messages.success(request, f'{email} has been unsubscribed from our newsletter.')
        except NewsletterSubscriber.DoesNotExist:
            messages.info(request, 'This email was not subscribed to our newsletter.')

        return super().get(request, *args, **kwargs)


class PrivacyPolicyView(TemplateView):
    """Privacy Policy page"""
    template_name = 'core/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        return context


class TermsOfServiceView(TemplateView):
    """Terms of Service page"""
    template_name = 'core/terms_of_service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        return context


class SafetyTrustView(TemplateView):
    """Safety & Trust page"""
    template_name = 'core/safety_trust.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()

        # Get verification process steps
        context['verification_steps'] = [
            {'step': 1, 'title': 'ID Verification', 'description': 'Government-issued ID validation'},
            {'step': 2, 'title': 'Skill Assessment', 'description': 'Trade-specific competency evaluation'},
            {'step': 3, 'title': 'Reference Checks', 'description': 'Contacting previous clients'},
            {'step': 4, 'title': 'Document Review', 'description': 'Certificates and portfolio verification'},
            {'step': 5, 'title': 'Background Check', 'description': 'Security and integrity screening'},
        ]

        return context


class HelpCenterView(TemplateView):
    """Help Center page"""
    template_name = 'core/help_center.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        context['faqs'] = FAQ.objects.filter(is_active=True)
        return context


class FAQView(ListView):
    """FAQ page with categorized questions"""
    template_name = 'core/faq.html'
    context_object_name = 'faqs'

    def get_queryset(self):
        """Get FAQs grouped by category"""
        return FAQ.objects.filter(is_active=True).order_by('category', 'order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()

        # Group FAQs by category
        faqs_by_category = {}
        for faq in context['faqs']:
            category = faq.get_category_display()
            if category not in faqs_by_category:
                faqs_by_category[category] = []
            faqs_by_category[category].append(faq)

        context['faqs_by_category'] = faqs_by_category
        return context


class SearchView(TemplateView):
    """Site search functionality"""
    template_name = 'core/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()

        query = self.request.GET.get('q', '')
        context['query'] = query

        if query:
            # Search across multiple models (simplified version)
            # In production, you might use Django Haystack or PostgreSQL Full Text Search
            from projects.models import Project
            from users.models import ArtisanProfile

            # Search projects
            projects = Project.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__icontains=query)
            ).filter(status='posted')[:10]

            # Search artisans
            artisans = ArtisanProfile.objects.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(trade__icontains=query) |
                Q(skills__icontains=query)
            ).filter(is_verified=True)[:10]

            # Search FAQs
            faqs = FAQ.objects.filter(
                Q(question__icontains=query) |
                Q(answer__icontains=query)
            ).filter(is_active=True)[:10]

            context['projects'] = projects
            context['artisans'] = artisans
            context['faqs'] = faqs
            context['has_results'] = any([projects.exists(), artisans.exists(), faqs.exists()])

        return context


class Error404View(TemplateView):
    """Custom 404 error page"""
    template_name = 'core/404.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = 404
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        return context


class Error500View(TemplateView):
    """Custom 500 error page"""
    template_name = 'core/500.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = 500
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSetting.objects.first()
        return context


