from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filter for custom dictionary return in template
    """
    return dictionary.get(key)