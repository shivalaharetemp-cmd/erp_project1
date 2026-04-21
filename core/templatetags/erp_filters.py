from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter and return list."""
    if isinstance(value, str):
        return value.split(delimiter)
    return value


@register.filter
def range_filter(value):
    """Return range of integers. Usage: 3|range_filter -> [0, 1, 2]"""
    return range(value)


@register.filter
def mul(value, arg):
    """Multiply two values."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary. Usage: mydict|get_item:key"""
    if isinstance(dictionary, dict):
        return dictionary.get(str(key))
    return None


@register.filter
def cut(value, arg):
    """Remove all occurrences of arg from string."""
    return str(value).replace(arg, '')
