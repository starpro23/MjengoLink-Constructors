"""
URL Configuration for Core App
Defines URL patterns for:
- Public pages (Home, About, Services, Contact, How It Works)
- Contact form processing
- Newsletter subscription
- Static information pages
"""

from django.urls import path
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from . import views
# from .sitemaps import StaticViewSitemap

app_name = 'core'

# sitemaps = {
#     'static': StaticViewSitemap,
# }

urlpatterns = [
    # Public Pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('how-it-works/', views.HowItWorksView.as_view(), name='how-it-works'),

    # Information Pages
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms'),
    path('safety-trust/', views.SafetyTrustView.as_view(), name='safety'),
    path('help-center/', views.HelpCenterView.as_view(), name='help-center'),
    path('faq/', views.FAQView.as_view(), name='faq'),

    # Form Processing
    path('contact/submit/', views.ContactSubmitView.as_view(), name='contact_submit'),
    path('newsletter/subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<str:email>/', views.NewsletterUnsubscribeView.as_view(),
         name='newsletter_unsubscribe'),


    # Legal & Compliance
    path('cancellation-policy/', TemplateView.as_view(template_name='core/cancellation_policy.html'),
         name='cancellation-policy'),
    path('refund-policy/', TemplateView.as_view(template_name='core/refund_policy.html'), name='refund-policy'),

    # Sitemap & SEO
    # path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='core/robots.txt', content_type='text/plain'),
         name='robots.txt'),

    # Error Pages (custom handlers)
    path('error/404/', views.Error404View.as_view(), name='error_404'),
    path('error/500/', views.Error500View.as_view(), name='error_500'),

    # Search
    path('search/', views.SearchView.as_view(), name='search'),
]
