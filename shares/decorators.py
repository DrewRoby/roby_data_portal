from functools import wraps
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from .models import ShareableInterface

def share_permission_required(permission_level='VIEW'):
    """
    Decorator that checks if a user has the required permission level for a shared object.
    
    Usage:
    @share_permission_required('EDIT')
    def my_view(request, story_id):
        # View code here
        
    The decorator expects that one of the view arguments ends with '_id' and represents
    the object ID that needs permission checking.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Find the object ID in the kwargs
            object_id = None
            model_type = None
            
            for key, value in kwargs.items():
                if key.endswith('_id'):
                    object_id = value
                    model_type = key.replace('_id', '')
                    break
            
            if not object_id:
                # No ID found, can't check permissions
                return view_func(request, *args, **kwargs)
            
            # Get the app name
            app_name = request.resolver_match.app_name
            
            # Find the correct model for this view
            model_class = None
            
            # Try to find the model for this app and object type
            for content_type in ContentType.objects.filter(app_label=app_name):
                model_cls = content_type.model_class()
                if hasattr(model_cls, '_meta') and model_cls._meta.model_name == model_type:
                    model_class = model_cls
                    break
            
            if not model_class or not issubclass(model_class, ShareableInterface):
                # Not a shareable model, proceed with the view
                return view_func(request, *args, **kwargs)
            
            # Get the object
            obj = get_object_or_404(model_class, pk=object_id)
            
            # Skip permission check if the user is the owner
            if hasattr(obj, 'user') and request.user.is_authenticated and obj.user == request.user:
                return view_func(request, *args, **kwargs)
            
            # Check permissions
            user_permission = obj.get_share_permissions(request.user)
            
            # If no permission, deny access
            if not user_permission:
                raise Http404("Object not found or you don't have permission to access it.")
            
            # Check if user has sufficient permission level
            permission_levels = ['VIEW', 'COMMENT', 'EDIT', 'ADMIN']
            required_level_index = permission_levels.index(permission_level)
            user_level_index = permission_levels.index(user_permission)
            
            if user_level_index < required_level_index:
                raise PermissionDenied(f"You need {permission_level} permission for this action.")
            
            # Permission check passed, proceed with the view
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator

def owner_or_permission_required(permission_level='VIEW', owner_field='user'):
    """
    Decorator that checks if the user is the owner or has the required permission.
    
    Usage:
    @owner_or_permission_required('EDIT', owner_field='author')
    def my_view(request, story_id):
        # View code here
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Find the object ID in the kwargs
            object_id = None
            model_type = None
            
            for key, value in kwargs.items():
                if key.endswith('_id'):
                    object_id = value
                    model_type = key.replace('_id', '')
                    break
            
            if not object_id:
                # No ID found, can't check permissions
                return view_func(request, *args, **kwargs)
                
            # Get the app name
            app_name = request.resolver_match.app_name
            
            # Find the correct model for this view
            model_class = None
            
            # Try to find the model for this app and object type
            for content_type in ContentType.objects.filter(app_label=app_name):
                model_cls = content_type.model_class()
                if hasattr(model_cls, '_meta') and model_cls._meta.model_name == model_type:
                    model_class = model_cls
                    break
            
            if not model_class:
                # Model not found, proceed with the view
                return view_func(request, *args, **kwargs)
            
            # Get the object
            obj = get_object_or_404(model_class, pk=object_id)
            
            # Check if user is the owner
            if (hasattr(obj, owner_field) and 
                request.user.is_authenticated and 
                getattr(obj, owner_field) == request.user):
                return view_func(request, *args, **kwargs)
            
            # If not the owner and not a shareable interface, deny access
            if not issubclass(model_class, ShareableInterface):
                raise PermissionDenied("You don't have permission to access this object.")
            
            # Check shared permissions
            user_permission = obj.get_share_permissions(request.user)
            
            # If no permission, deny access
            if not user_permission:
                raise Http404("Object not found or you don't have permission to access it.")
            
            # Check if user has sufficient permission level
            permission_levels = ['VIEW', 'COMMENT', 'EDIT', 'ADMIN']
            required_level_index = permission_levels.index(permission_level)
            user_level_index = permission_levels.index(user_permission)
            
            if user_level_index < required_level_index:
                raise PermissionDenied(f"You need {permission_level} permission for this action.")
            
            # Permission check passed, proceed with the view
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator