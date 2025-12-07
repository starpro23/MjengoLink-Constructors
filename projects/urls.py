"""
URL configuration for projects app
"""

from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'projects'

urlpatterns = [
    # Project views
    path('', views.ProjectListView.as_view(), name='list'),
    path('browse/', views.BrowseProjectsView.as_view(), name='browse'),
    path('search/', views.ProjectSearchView.as_view(), name='search'),
    path('create/', views.ProjectCreateView.as_view(), name='create'),
# In your urls.py
    path('my-projects/', views.MyProjectsView.as_view(), name='my_projects'),
    path('dashboard/', views.ProjectDashboardView.as_view(), name='dashboard'),

    # Project detail and management
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='delete'),
    path('<int:project_id>/status/', views.ProjectStatusUpdateView.as_view(), name='update_status'),

    # Bid views
    path('<int:project_id>/bid/', views.BidCreateView.as_view(), name='bid_create'),
    path('<int:project_id>/bids/', views.BidListView.as_view(), name='bid_list'),
    path('bids/<int:pk>/', views.BidDetailView.as_view(), name='bid_detail'),
    path('bids/<int:pk>/accept/', views.BidAcceptView.as_view(), name='bid_accept'),
    path('bids/<int:pk>/reject/', views.BidRejectView.as_view(), name='bid_reject'),
    path('bids/<int:pk>/withdraw/', views.BidWithdrawView.as_view(), name='bid_withdraw'),
    path('my-bids/', views.MyBidsView.as_view(), name='my_bids'),

    # Message views
    path('<int:project_id>/message/', views.MessageCreateView.as_view(), name='message_create'),
    path('<int:project_id>/conversation/', views.ConversationView.as_view(), name='conversation'),

    # Milestone views
    path('<int:project_id>/milestone/', views.MilestoneCreateView.as_view(), name='milestone_create'),
    path('milestones/<int:pk>/update/', views.MilestoneUpdateView.as_view(), name='milestone_update'),

    # Review views
    path('<int:project_id>/review/', views.ReviewCreateView.as_view(), name='review_create'),

    # AJAX/API endpoints
    path('<int:project_id>/images/', views.ProjectImageView.as_view(), name='project_images'),
    path('<int:project_id>/bid-stats/', views.get_bid_stats, name='bid_stats'),
    path('messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    path('unread-count/', views.get_unread_message_count, name='unread_count'),
]