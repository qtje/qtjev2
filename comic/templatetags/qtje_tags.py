from django import template
from django.utils.http import urlencode
import markdown
import urllib

register = template.Library()

@register.filter(name='render_markdown')
def render_markdown(value):
    if value == None: return ''
    md = markdown.Markdown(extensions=['extra', 'sane_lists', 'nl2br'])
    return md.convert(value)

