def user_apps(request):
    """
    Context processor to provide user's accessible apps to all templates.
    """
    if not request.user.is_authenticated:
        return {'user_apps': []}
    
    from .models import UserAppAccess, App
    
    # Get apps that the user has access to
    user_apps = App.objects.filter(
        id__in=UserAppAccess.objects.filter(user=request.user).values_list('app_id', flat=True)
    ).order_by('order', 'name')
    
    # If no specific apps are assigned, fall back to default apps
    if not user_apps.exists():
        user_apps = App.objects.filter(is_default=True).order_by('order', 'name')
    
    return {'user_apps': user_apps}