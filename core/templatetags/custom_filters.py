from urllib.parse import unquote

from django import template


register = template.Library()

@register.filter
def pretty(text):
    return unquote(
        text
    ).replace("\n", "")
