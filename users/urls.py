# users/urls.py
"""
URLs for Users app (MVP)
Only essential URLs for authentication and profiles
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard and Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/artisan/', views.artisan_profile, name='artisan_profile'),

    # ADD THESE MISSING URLS:
    path('my-projects/', views.my_projects_view, name='my_projects'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('profile/picture/', views.update_profile_picture, name='update_profile_picture'),
    path('portfolio/add/', views.add_portfolio_image, name='add_portfolio_image'),
    path('portfolio-image/<int:image_id>/delete/', views.delete_portfolio_image, name='delete_portfolio_image'),

    # Password reset (using Django's built-in)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]