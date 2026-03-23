from urllib.parse import unquote

from django import template


register = template.Library()

@register.filter
def pretty(text):
    if text == "\n":
        return
    prettier = unquote(
        text
    ).replace("\n", "")
    return prettier
