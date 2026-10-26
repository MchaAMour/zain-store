from django import template
register = template.Library()
@register.filter
def eur(cents):
    return f"€{(cents or 0) / 100:,.2f}"
