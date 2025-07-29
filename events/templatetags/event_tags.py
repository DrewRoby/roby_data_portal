from django import template
from events.models import EventInvitation
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.simple_tag
def get_user_invitation(event, user):
    """Get the user's invitation for an event, if it exists."""
    if not user or not user.is_authenticated:
        return None
    
    try:
        return EventInvitation.objects.get(event=event, invitee=user)
    except EventInvitation.DoesNotExist:
        return None

@register.filter
def can_suggest_agenda(event, user):
    """Check if user can suggest agenda items for this event."""
    return event.can_user_suggest_agenda_items(user)

@register.filter
def can_move_suggestions(event, user):
    """Check if user can move suggestions to agenda."""
    return event.can_user_move_suggestions(user)

@register.filter
def get_user_permission(event, user):
    """Get user's permission level for this event."""
    return event.get_user_permission(user)

@register.simple_tag
def get_suggestion_box(event):
    """Get the suggestion box space for an event."""
    return event.spaces.filter(space_type='suggestion_box').first()

@register.filter
def can_move_agenda_item(agenda_item, user):
    """Check if user can move this specific agenda item."""
    event = agenda_item.space.event
    user_permission = event.get_user_permission(user)
    
    if not user_permission:
        return False
    
    # If item is in suggestion box, need admin permission
    if agenda_item.space.space_type == 'suggestion_box':
        return event.can_user_move_suggestions(user)
    
    # For normal agenda items, need edit permission
    return user_permission in ['EDIT', 'ADMIN']

@register.filter 
def has_moveable_spaces(event, current_space):
    """Check if there are other spaces to move to."""
    return event.spaces.exclude(pk=current_space.pk).exists()