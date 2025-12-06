"""
Sitemap Configuration for Core App
Defines XML sitemaps for SEO optimization:
- Static pages sitemap
- Dynamic content sitemap
- SEO metadata for pages
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages
    Defines priority, changefreq, and lastmod for static pages
    """

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        """List of static page URLs"""
        return [
            'core:home',
            'core:about',
            'core:services',
            'core:contact',
            'core:how-it-works',
            'core:privacy-policy',
            'core:terms',
            'core:safety',
            'core:help-center',
            'core:faq',
        ]

    def location(self, item):
        """Get URL for each item"""
        return reverse(item)

    def lastmod(self, item):
        """Last modification date (static pages don't change often)"""
        from datetime import datetime
        return datetime.now()


class DynamicContentSitemap(Sitemap):
    """
    Base class for dynamic content sitemaps
    To be extended by other apps
    """

    changefreq = "daily"
    priority = 0.6

    def items(self):
        """To be implemented by child classes"""
        return []

    def lastmod(self, obj):
        """Get last modified date from object"""
        if hasattr(obj, 'updated_at'):
            return obj.updated_at
        elif hasattr(obj, 'created_at'):
            return obj.created_at
        return None


# Note: Project and Artisan sitemaps will be defined in their respective apps
# and imported here or registered in the main sitemap configuration