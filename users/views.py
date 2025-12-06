"""
User Views for MVP
Only essential views: register, login, logout, profile
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, ArtisanProfileForm, LoginForm
from .models import ArtisanProfile

#
# def artisan_register(request):
#     """
#     Special registration flow for artisans
#     """
#     if request.user.is_authenticated:
#         # If user is already logged in and is an artisan, go to profile
#         if hasattr(request.user, 'profile') and request.user.profile.user_type == 'artisan':
#             return redirect('users:artisan_profile')
#         # If logged in but not artisan, go to profile edit
#         elif request.user.is_authenticated:
#             messages.info(request, 'Please update your profile to artisan type first.')
#             return redirect('users:profile_edit')
#
#     # For non-logged in users, redirect to regular registration
#     # but we'll pass a parameter to indicate artisan registration
#     messages.info(request, 'Please register first, then select "Artisan" as your user type.')
#     return redirect('users:register')


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
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})



def login_view(request):
    """
    User login - MVP
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')

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
    except:
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