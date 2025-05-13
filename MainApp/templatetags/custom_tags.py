# your_app/templatetags/custom_tags.py
from django import template
from urllib.parse import urlencode
register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0  # Return 0 if the multiplication fails
    
@register.filter
def sum_values(queryset, field_name):
    """
    Custom filter to sum values of a specific field in a queryset.
    Usage: queryset|sum_values:"field_name"
    """
    if queryset:
        return sum(getattr(item, field_name) for item in queryset if getattr(item, field_name) is not None)
    return 0


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return '?' + urlencode(query)

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)
