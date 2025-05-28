# myapp/templatetags/custom_filters.py
from django import template
from myapp.models import Post

register = template.Library()

@register.filter(name='has_liked')
def has_liked(post, user):
    return post.likes.filter(user=user).exists()
    