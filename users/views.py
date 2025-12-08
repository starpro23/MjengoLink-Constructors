# users/views.py
"""
User Views for MVP
Only essential views: register, login, logout, profile
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # ADD THIS IMPORT
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, ArtisanProfileForm, LoginForm
# At the top of users/views.py, add these imports:
from .models import ArtisanProfile, ArtisanDocument, AdminActionLog
def dashboard_view(request):
    return render(request, 'users/dashboard.html')


def register(request):
    """
    User registration - MVP
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')

            if user.profile.user_type == 'artisan':
                return redirect('users:artisan_profile')
            return redirect('home')
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """
    User login - MVP
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Debug print
        print(f"Login attempt - Username: {username}")

        # First try to authenticate with provided username
        user = authenticate(request, username=username, password=password)

        # If that fails, check if it's an email and try to authenticate
        if user is None and '@' in username:
            try:
                # Find user by email
                user_by_email = User.objects.get(email=username)
                # Try authenticating with actual username
                user = authenticate(request, username=user_by_email.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')

            # Redirect based on user type
            if hasattr(user, 'profile'):
                if user.profile.user_type == 'admin':
                    return redirect('admin_dashboard')
                elif user.profile.user_type == 'artisan':
                    return redirect('users:dashboard')
                else:
                    return redirect('projects:dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    """
    User logout - MVP
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    """
    View user profile - MVP
    """
    user = request.user
    profile = user.profile

    context = {
        'user': user,
        'profile': profile,
    }

    if profile.user_type == 'artisan':
        try:
            context['artisan_profile'] = user.artisan_profile
        except:
            pass

    return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request):
    """
    Edit user profile - MVP
    """
    profile = request.user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def artisan_profile(request):
    """
    Edit artisan profile - MVP
    """
    if request.user.profile.user_type != 'artisan':
        messages.error(request, 'Only artisans can access this page.')
        return redirect('users:profile')

    try:
        artisan_profile = request.user.artisan_profile
    except ArtisanProfile.DoesNotExist:
        artisan_profile = ArtisanProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ArtisanProfileForm(request.POST, instance=artisan_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Artisan profile updated!')
            return redirect('users:profile')
    else:
        form = ArtisanProfileForm(instance=artisan_profile)

    return render(request, 'users/artisan_profile.html', {'form': form})


@staff_member_required
def verification_queue(request):
    """Admin view to see artisan verification queue"""
    from django.utils import timezone
    from django.db.models import Count, Avg, Q

    # Get unverified artisans (ArtisanProfile where is_verified=False)
    pending_artisans = ArtisanProfile.objects.filter(
        is_verified=False
    ).select_related('user').prefetch_related('documents', 'references')

    # Get counts for different document statuses
    pending_docs = ArtisanDocument.objects.filter(status='pending').count()

    # Calculate basic stats
    total_artisans = ArtisanProfile.objects.count()
    verified_artisans = ArtisanProfile.objects.filter(is_verified=True).count()

    # Calculate today's metrics
    today = timezone.now().date()
    approved_today = ArtisanProfile.objects.filter(
        is_verified=True,
        verification_date__date=today
    ).count()

    # Create applications list for the template
    applications = []
    for artisan in pending_artisans:
        # Get artisan's documents
        documents = artisan.artisan.documents.all()

        # Get document status counts
        doc_counts = {
            'pending': documents.filter(status='pending').count(),
            'verified': documents.filter(status='verified').count(),
            'rejected': documents.filter(status='rejected').count(),
        }

        # Get references
        references = artisan.artisan.references.all()
        ref_positive = references.filter(rating__gte=4).count()

        # Calculate queue time
        if artisan.user.date_joined:
            queue_days = (timezone.now() - artisan.user.date_joined).days
            queue_hours = queue_days * 24
        else:
            queue_hours = 24

        # Calculate integrity score (simple heuristic)
        integrity_score = 0
        if doc_counts['verified'] > 0:
            integrity_score += 30
        if references.count() >= 2:
            integrity_score += 30
        if artisan.id_verified:
            integrity_score += 20
        if artisan.certifications:
            integrity_score += 20

        app_data = {
            'id': artisan.id,
            'user': artisan.user,
            'profile': artisan.user.profile,
            'artisan': artisan,
            'trade': artisan.get_trade_display(),
            'experience_years': artisan.experience_years,
            'status': 'pending',  # Default status
            'integrity_score': min(integrity_score, 100),
            'risk_flags': 0,  # Could calculate based on rejected docs, etc.
            'queue_time_hours': queue_hours,
            'created_at': artisan.user.date_joined,
            'documents': {
                'all': documents,
                'pending': documents.filter(status='pending'),
                'verified': documents.filter(status='verified'),
                'counts': doc_counts,
            },
            'references_verified': references.filter(contacted=True).count() > 0,
            'references_pending': references.filter(contacted=False).count(),
            'references_positive': ref_positive,
            'total_references': references.count(),
        }

        # Determine specific status based on documents
        if doc_counts['pending'] > 0:
            app_data['status'] = 'documents_review'
        elif references.filter(contacted=False).exists():
            app_data['status'] = 'reference_check'
        else:
            app_data['status'] = 'pending'

        applications.append(app_data)

    # Sort applications by queue time (oldest first)
    applications.sort(key=lambda x: x['queue_time_hours'], reverse=True)

    # Prepare stats for template
    stats = {
        'pending_count': pending_artisans.count(),
        'total_users': total_artisans,
        'approved_today': approved_today,
        'avg_verification_time': 24,  # Placeholder
        'approval_rate': round((verified_artisans / total_artisans * 100) if total_artisans > 0 else 0, 1),
        'fraud_detected': ArtisanDocument.objects.filter(status='rejected').count(),
        'integrity_score': 75,  # Placeholder average
        'verified_artisans': verified_artisans,
        'pending_docs': pending_docs,
    }

    context = {
        'applications': applications,
        'pending_count': pending_artisans.count(),
        'pending_verification': pending_artisans,  # For backward compatibility
        'verification_count': pending_artisans.count(),
        'title': 'Artisan Verification Queue',
        'stats': stats,
    }

    return render(request, 'admin/verification_queue.html', context)


@staff_member_required
def verify_artisan(request, artisan_id):
    """Approve artisan verification"""
    from django.utils import timezone
    from django.contrib import messages

    if request.method == 'POST':
        try:
            artisan = ArtisanProfile.objects.get(id=artisan_id)
            artisan.is_verified = True
            artisan.verification_date = timezone.now()
            artisan.verified_by = request.user
            artisan.save()

            # Log the action
            AdminActionLog.objects.create(
                admin=request.user,
                action_type='user_verification',
                description=f'Verified artisan {artisan.user.get_full_name()}',
                target_user=artisan.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            messages.success(request, f'Artisan {artisan.user.get_full_name()} has been verified!')
        except ArtisanProfile.DoesNotExist:
            messages.error(request, 'Artisan not found')

    return redirect('admin:verification_queue')


@staff_member_required
def reject_artisan(request, artisan_id):
    """Reject artisan verification"""
    from django.contrib import messages

    if request.method == 'POST':
        try:
            artisan = ArtisanProfile.objects.get(id=artisan_id)
            reason = request.POST.get('reason', '')

            # Log the rejection
            AdminActionLog.objects.create(
                admin=request.user,
                action_type='user_verification',
                description=f'Rejected artisan {artisan.user.get_full_name()}. Reason: {reason}',
                target_user=artisan.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # You might want to send email notification here

            messages.warning(request, f'Artisan {artisan.user.get_full_name()} verification rejected.')
        except ArtisanProfile.DoesNotExist:
            messages.error(request, 'Artisan not found')

    return redirect('admin:verification_queue')


# ADD THESE VIEWS TO users/views.py:

@login_required
def my_projects_view(request):
    """View user's projects"""
    from projects.models import Project
    user = request.user

    if user.profile.user_type == 'homeowner':
        projects = Project.objects.filter(homeowner=user)
    elif user.profile.user_type == 'artisan':
        projects = Project.objects.filter(assigned_to=user)
    else:
        projects = Project.objects.none()

    return render(request, 'users/my_projects.html', {
        'projects': projects,
        'title': 'My Projects',
    })


@login_required
def settings_view(request):
    """User settings page"""
    return render(request, 'users/settings.html', {'title': 'Settings'})


@login_required
def profile_update_view(request):
    """Update user profile"""
    if request.method == 'POST':
        user = request.user
        profile = user.profile

        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        # Update profile fields
        profile.phone = request.POST.get('phone', profile.phone)
        profile.location = request.POST.get('location', profile.location)
        profile.bio = request.POST.get('bio', profile.bio)

        # Update profile picture if provided
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        # Update artisan profile if applicable
        if profile.user_type == 'artisan':
            try:
                artisan = user.artisan_profile
                artisan.trade = request.POST.get('trade', artisan.trade)
                artisan.experience_years = request.POST.get('experience', artisan.experience_years)
                artisan.skills = request.POST.get('skills', artisan.skills)
                artisan.certifications = request.POST.get('certifications', artisan.certifications)
                artisan.save()
            except:
                pass

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')

    return redirect('users:profile')


@login_required
def update_profile_picture(request):
    """Update profile picture only"""
    if request.method == 'POST':
        profile = request.user.profile
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            messages.success(request, 'Profile picture updated!')
    return redirect('users:profile')


@login_required
def add_portfolio_image(request):
    """Add portfolio images for artisans"""
    if request.method == 'POST' and request.user.profile.user_type == 'artisan':
        from .models import ArtisanPortfolioImage
        images = request.FILES.getlist('portfolio_images')

        for image in images[:10]:  # Limit to 10 images
            ArtisanPortfolioImage.objects.create(
                artisan=request.user,
                image=image
            )

        messages.success(request, 'Portfolio images added!')

    return redirect('users:profile')


@login_required
def delete_portfolio_image(request, image_id):
    """Delete portfolio image"""
    if request.method == 'DELETE' and request.user.profile.user_type == 'artisan':
        from .models import ArtisanPortfolioImage
        try:
            image = ArtisanPortfolioImage.objects.get(id=image_id, artisan=request.user)
            image.delete()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False}, status=404)

    return JsonResponse({'success': False}, status=400)