from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.conf import settings

from .models import Share, ShareableInterface
from django.contrib.contenttypes.models import ContentType

class SharePermissionMiddleware:
    """
    Middleware that checks if a user has permission to access a shared resource.
    This is added in addition to the standard Django authentication middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.process_request(request)
        if response:
            return response
        
        # Get response from the view
        response = self.get_response(request)
        
        return response
    
    def process_request(self, request):
        # Skip admin, static, and media URLs
        if any(request.path.startswith(prefix) for prefix in ['/admin/', '/static/', '/media/']):
            return None
        
        # Skip the share view itself and authentication views
        if request.path.startswith('/shares/') or request.path.startswith('/login/'):
            return None
        
        try:
            # Try to resolve the URL to get view information
            resolver_match = resolve(request.path)
            
            # Get the view's kwargs
            view_kwargs = resolver_match.kwargs
            
            # Look for app and model pattern arguments
            # This assumes your views follow a pattern where object ID is passed as a kwarg
            object_id = None
            for key, value in view_kwargs.items():
                if key.endswith('_id'):
                    object_id = value
                    model_type = key.replace('_id', '')
                    break
            
            if not object_id:
                # No ID found, no permission needed (probably a list view)
                return None
                
            # Get the app and model from the resolved URL
            app_name = resolver_match.app_name
            
            # If no app name, we can't determine the model, so skip middleware check
            if not app_name:
                return None
                
            # Try to find a model matching the URL pattern
            try:
                # This is a simplified approach - in a real app, you might need a mapping
                if hasattr(settings, 'SHAREABLE_MODELS'):
                    # Get model from settings mapping
                    model_mapping = settings.SHAREABLE_MODELS.get(app_name, {})
                    model_class = model_mapping.get(model_type)

                    if not model_class:
                        return None
                else:
                    # No explicit mapping, try looking up all models
                    # This is less efficient but more flexible
                    for content_type in ContentType.objects.filter(app_label=app_name):
                        model_class = content_type.model_class()
                        if issubclass(model_class, ShareableInterface):
                            try:
                                # Try to get object with this ID
                                obj = model_class.objects.get(pk=object_id)
                                # If we found it, we have the right model
                                break
                            except model_class.DoesNotExist:
                                continue
                    else:
                        # No matching model found
                        return None
                
                # Get the object
                obj = model_class.objects.get(pk=object_id)
                
                # Skip permission check if the user is the owner
                if hasattr(obj, 'user') and request.user.is_authenticated and obj.user == request.user:
                    return None
                
                # Check if the object is shared
                permission = obj.get_share_permissions(request.user)
                
                # If no permission found, require authentication
                if not permission:
                    if not request.user.is_authenticated:
                        return redirect_to_login(request.path)
                    else:
                        # User is authenticated but has no permission
                        raise Http404("Object not found or you don't have permission to view it.")
                
                # If this is a write operation but user only has read permission
                if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and permission == 'VIEW':
                    # Return 403 Forbidden
                    raise Http404("You don't have permission to perform this action.")
                    
            except (model_class.DoesNotExist, AttributeError):
                # Object doesn't exist or model has no shareable interface
                pass
                
        except Resolver404:
            # URL couldn't be resolved - likely a 404
            pass
            
        # Continue with the request
        return None