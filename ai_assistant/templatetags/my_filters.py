# ai_assistant/templatetags/my_filters.py
from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Splits the string by the given delimiter."""
    if isinstance(value, str):
        return value.split(delimiter)
    return []

# custom_tags.py
from django import template

register = template.Library()

@register.filter
def split_reasoning(value, separator):
    """
    Splits the value by the given separator and returns a list.
    """
    try:
        return value.split(separator)
    except Exception:
        return [value]
