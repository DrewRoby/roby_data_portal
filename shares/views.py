from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import Share, AccessLog, ShareableInterface
from .forms import ShareForm, SharePasswordForm

def access_share(request, share_id):
    """
    View for accessing a shared object.
    """
    share = get_object_or_404(Share, id=share_id)
    
    # Check if the share has expired
    if share.is_expired():
        return render(request, 'shares/error.html', {
            'error_message': 'This share has expired.'
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
            if str(share.id) not in verified_shares:
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
    created_shares = Share.objects.filter(created_by=request.user)
    received_shares = Share.objects.filter(shared_with=request.user, is_public=False)
    
    return render(request, 'shares/my_shares.html', {
        'created_shares': created_shares,
        'received_shares': received_shares,
    })

@login_required
def create_share(request, content_type_id, object_id):
    """
    View for creating a new share.
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
    # Typically would check if the user is the owner or has admin permissions
    if hasattr(obj, 'user') and obj.user != request.user:
        # Check for existing shares that give admin permission
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
                    # Use the custom date from the form
                    share.expires_at = form.cleaned_data['custom_expiry']
                else:
                    # Convert duration value (in days) to timedelta
                    days = int(form.cleaned_data['duration'])
                    share.expires_at = timezone.now() + timezone.timedelta(days=days)
            
            share.save()
            
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
@require_POST
def delete_share(request, share_id):
    """
    View for deleting a share.
    """
    share = get_object_or_404(Share, id=share_id, created_by=request.user)
    share.delete()
    messages.success(request, "Share deleted successfully.")
    return redirect('shares:my_shares')

@login_required
def edit_share(request, share_id):
    """
    View for editing an existing share.
    """
    share = get_object_or_404(Share, id=share_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ShareForm(request.POST, instance=share)
        if form.is_valid():
            updated_share = form.save(commit=False)
            
            # Set expiration date from form
            if form.cleaned_data['duration']:
                if form.cleaned_data['duration'] == 'custom':
                    # Use the custom date from the form
                    updated_share.expires_at = form.cleaned_data['custom_expiry']
                else:
                    # Convert duration value (in days) to timedelta
                    days = int(form.cleaned_data['duration'])
                    updated_share.expires_at = timezone.now() + timezone.timedelta(days=days)
            
            updated_share.save()
            
            messages.success(request, "Share updated successfully.")
            return redirect('shares:my_shares')
    else:
        # Determine the duration setting based on current expiry
        if share.expires_at:
            days_diff = (share.expires_at - timezone.now()).days
            if days_diff in [1, 7, 30, 90, 365]:
                initial_duration = str(days_diff)
            else:
                initial_duration = 'custom'
        else:
            initial_duration = None
            
        initial_data = {
            'duration': initial_duration,
            'custom_expiry': share.expires_at,
        }
        form = ShareForm(instance=share, initial=initial_data)
    
    return render(request, 'shares/edit_share.html', {
        'form': form,
        'share': share,
    })

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