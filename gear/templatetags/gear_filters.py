from django import template
from gear.models import Library, Collection, Item
import builtins

register = template.Library()


@register.filter
def isinstance(value, arg):

    if arg == "Library":
        return builtins.isinstance(value, Library)
    elif arg == "Collection":
        return builtins.isinstance(value, Collection)
    elif arg == "Item":
        return builtins.isinstance(value, Item)
    return False
