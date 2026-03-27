from django import template

register = template.Library()

@register.filter
def verbose_name(obj):
    """Get the verbose name of a model object."""
    try:
        return obj._meta.verbose_name
    except AttributeError:
        return str(type(obj).__name__)

@register.filter
def model_name(obj):
    """Get the model name of an object."""
    try:
        return obj._meta.model_name
    except AttributeError:
        return str(type(obj).__name__).lower()
