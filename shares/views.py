from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import Share, ShareEmailNotification, ShareableInterface, AccessLog
from .forms import ShareForm, ResendEmailForm
from .services import ShareEmailService
import logging

logger = logging.getLogger(__name__)

def access_share(request, share_id):
    """
    View for accessing a shared object.
    """
    share = get_object_or_404(Share, id=share_id)
    
    # Check if the share has expired
    if share.is_expired():
        return render(request, 'shares/error.html', {
            'error_message': 'This share has expired.',
            'share': share,
        })
    
    # Check if the user has access (bypass password check for the owner)
    user_is_owner = request.user.is_authenticated and request.user == share.created_by
    
    # If it's a password-protected share and user is not the owner
    if share.password and not user_is_owner:
        # If the password form was submitted
        if request.method == 'POST':
            form = SharePasswordForm(request.POST)
            if form.is_valid():
                # Check if password matches
                if form.cleaned_data['password'] == share.password:
                    # Store password verification in session
                    if not request.session.get('verified_shares'):
                        request.session['verified_shares'] = []
                    if str(share.id) not in request.session['verified_shares']:
                        request.session['verified_shares'].append(str(share.id))
                    
                    # Redirect to avoid form resubmission
                    return redirect('shares:access_share', share_id=share.id)
                else:
                    form.add_error('password', 'Incorrect password')
            
        else:
            # Check if password is already verified via session
            verified_shares = request.session.get('verified_shares', [])
            if str(share.id) not in verified_shares and not share.is_public:
                # Show password form
                return render(request, 'shares/password_form.html', {
                    'share': share,
                    'form': SharePasswordForm()
                })
    
    # If we get here, the user has passed all required checks
    
    # Check if the user has access
    user_has_access = share.is_public or user_is_owner or (
        request.user.is_authenticated and share.shared_with == request.user
    )
    
    if not user_has_access:
        raise PermissionDenied("You don't have permission to access this shared content.")
    
    # Log the access
    AccessLog.objects.create(
        share=share,
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        password_used=share.password is not None
    )
    
    # Increment access count
    share.increment_access_count()
    
    # Get the shared object
    shared_object = share.shared_object
    
    # Assuming each model has a method to return its share template
    # or we have a convention for template names
    try:
        app_name = shared_object._meta.app_label
        model_name = shared_object._meta.model_name
        template_name = f'{app_name}/shared_{model_name}.html'
        
        # Try to get the shareable context from the model if it has that method
        if hasattr(shared_object, 'get_shareable_context'):
            context = shared_object.get_shareable_context(request, share)
        else:
            # Default context
            context = {
                'object': shared_object,
                'share': share,
                'permission': share.permission_type,
            }
        
        return render(request, template_name, context)
    except Exception as e:
        # Fallback to a generic template
        return render(request, 'shares/shared_object.html', {
            'object': shared_object,
            'share': share,
            'error': str(e),
            'permission': share.permission_type,
        })

@login_required
def my_shares(request):
    """
    View for displaying all shares created by the current user.
    """
    now = timezone.now()
    
    # Get all shares created by the user
    all_created_shares = Share.objects.filter(created_by=request.user)
    
    # Separate active and expired shares
    created_shares = all_created_shares.filter(
        Q(expires_at__gt=now) | Q(expires_at__isnull=True)
    )
    expired_shares = all_created_shares.filter(expires_at__lte=now)
    
    # Get shares received by the user (keeping existing filtering)
    received_shares = Share.objects.filter(
        shared_with=request.user, 
        is_public=False,
        expires_at__gt=now
    )
    
    return render(request, 'shares/my_shares.html', {
        'created_shares': created_shares,
        'expired_shares': expired_shares,
        'received_shares': received_shares,
    })

@login_required
def create_share(request, content_type_id, object_id):
    """
    View for creating a new share with email notification support.
    """
    # Get the content type and check it exists
    content_type = get_object_or_404(ContentType, id=content_type_id)
    
    # Get the model class
    model_class = content_type.model_class()
    
    # Check if the model inherits from ShareableInterface
    if not issubclass(model_class, ShareableInterface):
        raise Http404("This object cannot be shared.")
    
    # Get the object to be shared
    try:
        obj = model_class.objects.get(id=object_id)
    except model_class.DoesNotExist:
        raise Http404("Object not found.")
    
    # Check if the user has permission to share this object
    if hasattr(obj, 'user') and obj.user != request.user:
        if obj.get_share_permissions(request.user) != 'ADMIN':
            raise PermissionDenied("You don't have permission to share this object.")
    
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            share = form.save(commit=False)
            share.content_type = content_type
            share.object_id = object_id
            share.created_by = request.user
            
            # Set expiration date from form
            if form.cleaned_data['duration']:
                if form.cleaned_data['duration'] == 'custom':
                    share.expires_at = form.cleaned_data['custom_expiry']
                else:
                    days = int(form.cleaned_data['duration'])
                    share.expires_at = timezone.now() + timezone.timedelta(days=days)
            
            share.save()
            
            # Handle email notifications for public shares
            if share.is_public and form.cleaned_data.get('email_recipients'):
                email_list = form.get_email_list()
                if email_list:
                    results = ShareEmailService.send_multiple_notifications(
                        share, email_list, request.user, request
                    )
                    
                    # Provide feedback to user
                    if results['success_count'] > 0:
                        messages.success(
                            request, 
                            f"Share created successfully! Email notifications sent to {results['success_count']} recipient(s)."
                        )
                    
                    if results['duplicate_count'] > 0:
                        messages.info(
                            request,
                            f"{results['duplicate_count']} recipient(s) were already notified about this share."
                        )
                    
                    if results['failure_count'] > 0:
                        messages.warning(
                            request,
                            f"Failed to send {results['failure_count']} email notification(s). Please check the email addresses and try again."
                        )
            else:
                messages.success(request, "Share created successfully.")
            
            return redirect('shares:my_shares')
    else:
        # Initialize form with default values
        initial_data = {
            'name': obj.get_share_title(),
            'description': obj.get_share_description(),
            'duration': '30',  # Default to 30 days
        }
        form = ShareForm(initial=initial_data)
    
    return render(request, 'shares/create_share.html', {
        'form': form,
        'object': obj,
    })

@login_required
def edit_share(request, share_id):
    """
    View for editing an existing share with email management.
    """
    share = get_object_or_404(Share, id=share_id, created_by=request.user)
    
    # Get existing email notifications
    email_notifications = ShareEmailNotification.objects.filter(share=share).order_by('-sent_at')
    
    if request.method == 'POST':
        form = ShareForm(request.POST, instance=share)
        if form.is_valid():
            updated_share = form.save()
            
            # Handle new email notifications for public shares
            if updated_share.is_public and form.cleaned_data.get('email_recipients'):
                email_list = form.get_email_list()
                if email_list:
                    results = ShareEmailService.send_multiple_notifications(
                        updated_share, email_list, request.user, request
                    )
                    
                    # Provide feedback to user
                    if results['success_count'] > 0:
                        messages.success(
                            request, 
                            f"Share updated! Email notifications sent to {results['success_count']} new recipient(s)."
                        )
                    
                    if results['duplicate_count'] > 0:
                        messages.info(
                            request,
                            f"{results['duplicate_count']} recipient(s) were already notified about this share."
                        )
                    
                    if results['failure_count'] > 0:
                        messages.warning(
                            request,
                            f"Failed to send {results['failure_count']} email notification(s)."
                        )
            else:
                messages.success(request, "Share updated successfully.")
            
            return redirect('shares:edit_share', share_id=share.id)
    else:
        # Initialize form with current share data
        initial_data = {}
        if share.shared_with:
            initial_data['shared_with_username'] = share.shared_with.username
        
        form = ShareForm(instance=share, initial=initial_data)
    
    share_url = request.build_absolute_uri(share.get_absolute_url())

    context = {
        'form': form,
        'share': share,
        'share_url':share_url,
        'email_notifications': email_notifications,
    }
    
    return render(request, 'shares/edit_share.html', context)

@login_required
@require_POST
def resend_email(request, share_id):
    """
    View for resending an email notification to a specific address.
    """
    share = get_object_or_404(Share, id=share_id, created_by=request.user)
    
    if not share.is_public:
        messages.error(request, "Email notifications are only available for public shares.")
        return redirect('shares:edit_share', share_id=share.id)
    
    email_address = request.POST.get('email_address')
    if not email_address:
        messages.error(request, "Email address is required.")
        return redirect('shares:edit_share', share_id=share.id)
    
    # Resend the notification
    success, notification = ShareEmailService.resend_notification(
        share, email_address, request.user, request
    )
    
    if success:
        messages.success(request, f"Email notification resent to {email_address}.")
    else:
        messages.error(request, f"Failed to resend email notification to {email_address}.")
    
    return redirect('shares:edit_share', share_id=share.id)

@login_required
@require_POST
def delete_share(request, share_id):
    """
    View for deleting a share.
    """
    share = get_object_or_404(Share, id=share_id, created_by=request.user)
    share.delete()
    messages.success(request, "Share deleted successfully.")
    return redirect('shares:my_shares')

def shared_with_me(request):
    """
    View for displaying all shares shared with the current user.
    """
    if not request.user.is_authenticated:
        return redirect('portal:login')
    
    shares = Share.objects.filter(
        shared_with=request.user,
        is_public=False,
        expires_at__gt=timezone.now()
    )
    
    return render(request, 'shares/shared_with_me.html', {
        'shares': shares,
    })