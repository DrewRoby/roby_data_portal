from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from .forms import LoginForm, RegistrationForm
from .models import UserProfile, EmailVerificationToken
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import uuid

def home(request):
    """View for the home page."""
    return render(request, 'portal/guestpage.html')

def login_view(request):
    """View for user login."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if email is verified
                if hasattr(user, 'profile') and user.profile.is_email_verified:
                    login(request, user)
                    return redirect('home')  # Changed from 'dashboard' to 'home'
                else:
                    messages.error(request, 'Please verify your email address before logging in.')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    
    # Get registration form
    register_form = RegistrationForm()
    
    return render(request, 'portal/login.html', {
        'form': form, 
        'register_form': register_form
    })

def register(request):
    """View for user registration."""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create the user but don't save to DB yet
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_email_verified = False
            profile.save()
            
            # Create verification token
            token, created = EmailVerificationToken.objects.get_or_create(user=user)
            if not created:
                # Refresh token if it already exists
                token.token = uuid.uuid4()
                token.created_at = timezone.now()
                token.expires_at = None  # Will be set in save method
                token.save()
            
            # Send verification email
            send_verification_email(request, user, token)
            
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'portal/register.html', {'form': form})

def verify_email(request, token):
    """View for email verification."""
    # Get the token or return 404
    verification_token = get_object_or_404(EmailVerificationToken, token=token)
    
    # Check if token is expired
    if verification_token.is_expired:
        messages.error(request, 'Verification link has expired. Please request a new one.')
        return redirect('login')
    
    # Verify the user's email
    user = verification_token.user
    
    # Create profile if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.is_email_verified = True
    profile.save()
    
    # Delete the token as it's been used
    verification_token.delete()
    
    messages.success(request, 'Email verified successfully! You can now log in to your account.')
    return redirect('login')
    
def resend_verification(request):
    """View to resend verification email."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Create or refresh verification token
            token, created = EmailVerificationToken.objects.get_or_create(user=user)
            if not created:
                token.token = uuid.uuid4()
                token.created_at = timezone.now()
                token.expires_at = None
                token.save()
            
            # Send verification email
            send_verification_email(request, user, token)
            
            messages.success(request, 'Verification email has been resent. Please check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
    
    return redirect('login')

def send_verification_email(request, user, token):
    """Helper function to send verification email."""
    verification_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token.token})
    )
    
    subject = 'Verify your email for Roby Data Services'
    html_message = render_to_string('portal/email/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
        'expiry_hours': 48
    })
    
    plain_message = f"""
    Hi {user.first_name},
    
    Please verify your email address to activate your Roby Data Services account.
    
    Click the link below to verify (valid for 48 hours):
    {verification_url}
    
    If you didn't register for an account, please ignore this email.
    
    Thank you,
    Roby Data Services Team
    """
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )

@login_required
def get_homepage(request):
    """View for the user home page. Requires login."""
    return render(request, 'portal/home.html')
