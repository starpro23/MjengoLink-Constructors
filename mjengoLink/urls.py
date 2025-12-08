from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from users.views import verification_queue  # Direct import
from core.views import HomeView  # Import your HomeView
urlpatterns = [

# Custom admin URLs BEFORE the admin.urls
    path('admin/verification-queue/',
         admin.site.admin_view(verification_queue),
         name='verification_queue'),

    # Standard Django admin
    path('admin/', admin.site.urls),

    path('', HomeView.as_view(), name='home'),  # Add this line
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('projects/', include('projects.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)