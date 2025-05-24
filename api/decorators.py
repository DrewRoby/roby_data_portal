from functools import wraps
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework.response import Response
from .models import APIUsageLog
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
            
            # Check daily rate limit
            today = timezone.now().date()
            daily_key = f"api_daily_{user.id}_{today}"
            daily_count = cache.get(daily_key, 0)
            
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
                
                # Log successful API usage
                if response.status_code == 200:
                    # Increment daily counter
                    cache.set(daily_key, daily_count + 1, 86400)  # 24 hours
                    
                    # Log usage
                    result_count = 0
                    if hasattr(response, 'data') and 'total_found' in response.data:
                        result_count = response.data['total_found']
                    
                    APIUsageLog.objects.create(
                        user=user,
                        endpoint=endpoint_name,
                        request_data=request.data if hasattr(request, 'data') else None,
                        response_count=result_count,
                        success=True
                    )
                else:
                    # Log failed usage
                    APIUsageLog.objects.create(
                        user=user,
                        endpoint=endpoint_name,
                        request_data=request.data if hasattr(request, 'data') else None,
                        success=False,
                        error_message=f"HTTP {response.status_code}"
                    )
                
                return response
                
            except Exception as e:
                # Log error
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
