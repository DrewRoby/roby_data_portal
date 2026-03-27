# inventory/templatetags/inventory_filters.py
from django import template
import datetime

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Add the argument to the value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """Calculate value as a percentage of arg"""
    try:
        return (float(value) / float(arg) * 100) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0

@register.filter
def abs_value(value):
    """Return the absolute value"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def floatformat_with_default(value, arg=2):
    """Format a float with a specified number of decimal places, with a default value of 0"""
    try:
        return format(float(value), f'.{arg}f')
    except (ValueError, TypeError):
        return format(0, f'.{arg}f')