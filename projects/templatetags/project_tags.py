from django import template
from projects.models import Project

register = template.Library()

@register.filter
def skill_match(project, user):
    return project.get_skill_match(user)