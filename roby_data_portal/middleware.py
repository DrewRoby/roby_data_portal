# Create this file at: roby_data_portal/middleware.py

from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Public URLs that don't require authentication
        self.public_urls = [
            'login',
            'logout',
            'register',
            'guestpage',
            'verify_email',
            'resend_verification',
            'admin:index',
            'admin:login',
        ]
        
        # Paths that start with these prefixes will be exempt
        self.exempt_prefixes = [
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Let the view handle the request if the user is already authenticated
        if request.user.is_authenticated:
            return self.get_response(request)
            
        # Check if current path starts with any exempt prefix
        path = request.path_info
        if any(path.startswith(prefix) for prefix in self.exempt_prefixes):
            return self.get_response(request)
            
        # Check if current URL name is in the exempt list
        try:
            current_url_match = resolve(path)
            view_name = current_url_match.url_name
            namespace = current_url_match.namespace
            
            if namespace:
                view_path = f"{namespace}:{view_name}"
            else:
                view_path = view_name
                
            if view_path in self.public_urls or view_name in self.public_urls:
                return self.get_response(request)
        except:
            # If URL can't be resolved, just continue with the middleware
            pass
            
        # Redirect unauthenticated users to login
        login_url = reverse('portal:login')  # Use your actual login URL name
        return redirect(f"{login_url}?next={request.path}")