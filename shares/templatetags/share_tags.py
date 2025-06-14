"""
Example views integration with Storycraft app.
This shows how to use the decorators and sharing functionality in views.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from shares.decorators import share_permission_required, owner_or_permission_required
from shares.models import Share

from storycraft.models import Story, Character, Plot, Scene

from django import template


register = template.Library()


@register.simple_tag
def get_share_permission(obj, user):
    """
    Returns the permission level a user has for an object.
    
    Usage:
    {% get_share_permission object user as permission %}
    {% if permission == 'EDIT' %}
        <a href="{% url 'edit_object' object.id %}">Edit</a>
    {% endif %}
    """
    if hasattr(obj, 'get_share_permissions'):
        return obj.get_share_permissions(user)
    return None

@register.simple_tag
def get_content_type_id(obj):
    """
    Returns the content type ID for an object.
    
    Usage:
    {% get_content_type_id object as content_type_id %}
    <a href="{% url 'shares:create_share' content_type_id object.id %}">Share</a>
    """
    content_type = ContentType.objects.get_for_model(obj)
    return content_type.id

@register.inclusion_tag('shares/tags/share_button.html')
def share_button(obj, user, button_text="Share", css_class="btn btn-primary"):
    """
    Renders a share button if the user has permission to share the object.
    
    Usage:
    {% share_button object user "Share this" "btn btn-sm btn-primary" %}
    """
    content_type = ContentType.objects.get_for_model(obj)
    
    # Check if user has permission to share
    can_share = False
    
    # User is owner
    if hasattr(obj, 'user') and obj.user == user:
        can_share = True
    # User has admin permission
    elif hasattr(obj, 'get_share_permissions') and obj.get_share_permissions(user) == 'ADMIN':
        can_share = True
        
    return {
        'can_share': can_share,
        'content_type_id': content_type.id,
        'object_id': obj.id,
        'button_text': button_text,
        'css_class': css_class,
    }

@register.inclusion_tag('shares/tags/permission_badge.html')
def permission_badge(permission):
    """
    Renders a badge showing the permission level.
    
    Usage:
    {% permission_badge permission %}
    """
    badge_classes = {
        'VIEW': 'badge bg-info',
        'COMMENT': 'badge bg-primary',
        'EDIT': 'badge bg-success',
        'ADMIN': 'badge bg-danger',
    }
    
    return {
        'permission': permission,
        'badge_class': badge_classes.get(permission, 'badge bg-secondary'),
    }

@register.filter
def has_permission(obj, user):
    """
    Returns True if the user has any permission for the object.
    
    Usage:
    {% if object|has_permission:user %}
        <p>You have access to this object</p>
    {% endif %}
    """
    if hasattr(obj, 'get_share_permissions'):
        return obj.get_share_permissions(user) is not None
    return False

@register.filter
def has_permission_level(obj, args):
    """
    Returns True if the user has the specified permission level for the object.
    
    Usage:
    {% if object|has_permission_level:"user,EDIT" %}
        <a href="{% url 'edit_object' object.id %}">Edit</a>
    {% endif %}
    """
    parts = args.split(',')
    if len(parts) != 2:
        return False
        
    user, required_level = parts
    
    if not hasattr(obj, 'get_share_permissions'):
        return False
        
    user_permission = obj.get_share_permissions(user)
    
    if not user_permission:
        return False
        
    permission_levels = ['VIEW', 'COMMENT', 'EDIT', 'ADMIN']
    
    try:
        required_index = permission_levels.index(required_level)
        user_index = permission_levels.index(user_permission)
        return user_index >= required_index
    except ValueError:
        return False

@register.inclusion_tag('shares/tags/share_list.html')
def user_shares(user, limit=5):
    """
    Renders a list of shares created by the user.
    
    Usage:
    {% user_shares user 10 %}
    """
    shares = Share.objects.filter(created_by=user).order_by('-created_at')[:limit]
    return {'shares': shares}

@register.inclusion_tag('shares/tags/shared_with_me.html')
def shared_with_me(user, limit=5):
    """
    Renders a list of shares shared with the user.
    
    Usage:
    {% shared_with_me user 10 %}
    """
    shares = Share.objects.filter(shared_with=user).order_by('-created_at')[:limit]
    return {'shares': shares}

