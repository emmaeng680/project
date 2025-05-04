# from django.shortcuts import render, redirect
# from django.contrib.auth import login
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.views.decorators.csrf import ensure_csrf_cookie
# from django.db import transaction
# from .forms import (UserRegistrationForm, TechnicianProfileForm, 
#                    NeurologistProfileForm, PatientProfileForm, UserProfileUpdateForm)
# from .models import User
# import logging

# logger = logging.getLogger(__name__)

# @ensure_csrf_cookie
# def register(request):
#     """View for user registration with role-specific forms"""
#     if request.method == 'POST':
#         user_form = UserRegistrationForm(request.POST)
#         technician_form = TechnicianProfileForm(request.POST)
#         neurologist_form = NeurologistProfileForm(request.POST)
#         patient_form = PatientProfileForm(request.POST)
        
#         if user_form.is_valid():
#             with transaction.atomic():
#                 user = user_form.save()
                
#                 # Handle role-specific profile forms
#                 role = user.role
#                 if role == User.Role.TECHNICIAN and technician_form.is_valid():
#                     profile = technician_form.save(commit=False)
#                     profile.user = user
#                     profile.save()
#                 elif role == User.Role.NEUROLOGIST and neurologist_form.is_valid():
#                     profile = neurologist_form.save(commit=False)
#                     profile.user = user
#                     profile.save()
#                 elif role == User.Role.PATIENT and patient_form.is_valid():
#                     profile = patient_form.save(commit=False)
#                     profile.user = user
#                     profile.save()
                
#                 # Log the user in
#                 login(request, user)
#                 messages.success(request, f"Account created for {user.username}!")
                
#                 # Redirect to the home view which will then redirect based on role
#                 return redirect('home')
#         else:
#             messages.error(request, "Please correct the errors below.")
#     else:
#         user_form = UserRegistrationForm()
#         technician_form = TechnicianProfileForm()
#         neurologist_form = NeurologistProfileForm()
#         patient_form = PatientProfileForm()
    
#     return render(request, 'accounts/register.html', {
#         'user_form': user_form,
#         'technician_form': technician_form,
#         'neurologist_form': neurologist_form,
#         'patient_form': patient_form
#     })

# @login_required
# def profile(request):
#     """View for user profile page"""
#     user = request.user
    
#     if request.method == 'POST':
#         form = UserProfileUpdateForm(request.POST, instance=user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Your profile has been updated!")
#             return redirect('accounts:profile')
#     else:
#         form = UserProfileUpdateForm(instance=user)
    
#     # Get the role-specific profile if it exists
#     role_profile = None
#     if user.is_technician and hasattr(user, 'technician_profile'):
#         role_profile = user.technician_profile
#     elif user.is_neurologist and hasattr(user, 'neurologist_profile'):
#         role_profile = user.neurologist_profile
#     elif user.is_patient and hasattr(user, 'patient_profile'):
#         role_profile = user.patient_profile
    
#     return render(request, 'accounts/profile.html', {
#         'form': form,
#         'role_profile': role_profile
#     })

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from .forms import (UserRegistrationForm, TechnicianProfileForm, 
                   NeurologistProfileForm, PatientProfileForm, UserProfileUpdateForm)
from .models import User
import logging

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def register(request):
    """View for user registration with role-specific forms"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        technician_form = TechnicianProfileForm(request.POST)
        neurologist_form = NeurologistProfileForm(request.POST)
        patient_form = PatientProfileForm(request.POST)
        
        if user_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                
                # Handle role-specific profile forms
                role = user.role
                if role == User.Role.TECHNICIAN and technician_form.is_valid():
                    profile = technician_form.save(commit=False)
                    profile.user = user
                    profile.save()
                elif role == User.Role.NEUROLOGIST and neurologist_form.is_valid():
                    profile = neurologist_form.save(commit=False)
                    profile.user = user
                    profile.save()
                elif role == User.Role.PATIENT and patient_form.is_valid():
                    profile = patient_form.save(commit=False)
                    profile.user = user
                    profile.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, f"Account created for {user.username}!")
                
                # Redirect to the home view which will then redirect based on role
                return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserRegistrationForm()
        technician_form = TechnicianProfileForm()
        neurologist_form = NeurologistProfileForm()
        patient_form = PatientProfileForm()
    
    return render(request, 'accounts/register.html', {
        'user_form': user_form,
        'technician_form': technician_form,
        'neurologist_form': neurologist_form,
        'patient_form': patient_form
    })

# def user_login(request):
#     """Custom login view with detailed error messages"""
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         logger.debug(f"Login attempt for username: {username}")
        
#         user = authenticate(request, username=username, password=password)
        
#         if user is not None:
#             login(request, user)
#             logger.info(f"User {username} logged in successfully")
#             messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            
#             # Redirect to the appropriate page based on user role
#             if user.is_patient:
#                 return redirect('patients:dashboard')
#             elif user.is_technician:
#                 return redirect('consultations:technician_dashboard')
#             elif user.is_neurologist:
#                 return redirect('consultations:neurologist_dashboard')
#             else:
#                 return redirect('home')
#         else:
#             logger.warning(f"Failed login attempt for username: {username}")
#             messages.error(request, "Invalid username or password. Please try again.")
    
#     return render(request, 'registration/login.html')

def user_login(request):
    """Simplified login view for quick debugging"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"Login attempt for username: {username}")
        
        # Try to authenticate
        user = authenticate(request, username=username, password=password)
        
        # If authentication successful
        if user is not None:
            login(request, user)
            print(f"User {username} logged in successfully")
            messages.success(request, f"Welcome, {user.username}!")
            
            # Simple redirect - don't check roles for now
            return redirect('home')
        else:
            print(f"Failed login attempt for username: {username}")
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, 'registration/login.html')


@login_required
def profile(request):
    """View for user profile page"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('accounts:profile')
    else:
        form = UserProfileUpdateForm(instance=user)
    
    # Get the role-specific profile if it exists
    role_profile = None
    if user.is_technician and hasattr(user, 'technician_profile'):
        role_profile = user.technician_profile
    elif user.is_neurologist and hasattr(user, 'neurologist_profile'):
        role_profile = user.neurologist_profile
    elif user.is_patient and hasattr(user, 'patient_profile'):
        role_profile = user.patient_profile
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'role_profile': role_profile
    })

def emergency_login(request):
    """Emergency login function for demo purposes only"""
    from django.contrib.auth import login
    from accounts.models import User
    
    # Try to find the admin user
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        # If admin doesn't exist, find any user
        try:
            user = User.objects.first()
        except:
            return redirect('login')
    
    # Force login with this user
    login(request, user)
    return redirect('home')

def direct_login(request):
    """Emergency simplified login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"Login attempt for username: {username}")
        
        # Try to authenticate
        from django.contrib.auth import authenticate, login
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            print(f"User {username} logged in successfully")
            from django.shortcuts import redirect
            return redirect('home')
        else:
            print(f"Failed login attempt for {username}")
            # Make sure to return render here even if authentication fails
            from django.shortcuts import render
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    
    # For GET requests
    from django.shortcuts import render
    return render(request, 'registration/login.html')