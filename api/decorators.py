from functools import wraps
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework.response import Response
from .models import APIUsageLog
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def api_access_required(endpoint_name):
    """
    Decorator that combines authentication, permission checking, and rate limiting
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Check if user has API access enabled
            if not hasattr(user, 'profile') or not user.profile.api_access_enabled:
                logger.warning(f"API access denied for user {user.username} - not enabled")
                return Response({
                    'error': 'API access not enabled. Contact administrator for access.'
                }, status=403)
            
            # Check daily rate limit using database
            today = timezone.now().date()
            daily_count = APIUsageLog.objects.filter(
                user=user,
                endpoint=endpoint_name,
                timestamp__date=today,
                success=True
            ).count()
            
            if daily_count >= user.profile.api_daily_limit:
                logger.warning(f"Daily rate limit exceeded for user {user.username}")
                return Response({
                    'error': f'Daily limit of {user.profile.api_daily_limit} requests exceeded. Try again tomorrow.'
                }, status=429)
            
            # Check monthly rate limit
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_count = APIUsageLog.objects.filter(
                user=user,
                endpoint=endpoint_name,
                timestamp__gte=current_month,
                success=True
            ).count()
            
            if monthly_count >= user.profile.api_monthly_limit:
                logger.warning(f"Monthly rate limit exceeded for user {user.username}")
                return Response({
                    'error': f'Monthly limit of {user.profile.api_monthly_limit} requests exceeded.'
                }, status=429)
            
            # Execute the view
            try:
                response = view_func(request, *args, **kwargs)
                
                # Log API usage
                if response.status_code == 200:
                    result_count = 0
                    used_cache = False
                    
                    if hasattr(response, 'data'):
                        result_count = response.data.get('total_found', 0)
                        used_cache = response.data.get('from_cache', False)
                    
                    APIUsageLog.objects.create(
                        user=user,
                        endpoint=endpoint_name,
                        request_data=request.data if hasattr(request, 'data') else None,
                        response_count=result_count,
                        success=True,
                        used_cache=used_cache
                    )
                else:
                    APIUsageLog.objects.create(
                        user=user,
                        endpoint=endpoint_name,
                        request_data=request.data if hasattr(request, 'data') else None,
                        success=False,
                        error_message=f"HTTP {response.status_code}"
                    )
                
                return response
                
            except Exception as e:
                APIUsageLog.objects.create(
                    user=user,
                    endpoint=endpoint_name,
                    request_data=request.data if hasattr(request, 'data') else None,
                    success=False,
                    error_message=str(e)
                )
                logger.error(f"API error for user {user.username}: {str(e)}")
                raise
        
        return _wrapped_view
    return decorator