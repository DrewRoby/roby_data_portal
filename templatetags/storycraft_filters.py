from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Returns the value in the dictionary for the given key.
    Used to access character motivation data in templates.
    """
    if dictionary and key:
        try:
            return dictionary.get(key)
        except (AttributeError, KeyError, TypeError):
            return None
    return None