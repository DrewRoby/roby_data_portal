from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()

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
