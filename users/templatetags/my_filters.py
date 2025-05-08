from django import template

register = template.Library()


@register.filter(name='truncate_smart')
def truncate_smart(value, max_length=15):
    if len(value) <= max_length:
        return value

    # Try to split at last space within max_length
    truncated = value[:max_length]
    if ' ' in truncated:
        return truncated.rsplit(' ', 1)[0] + '...'

    return truncated + '...'