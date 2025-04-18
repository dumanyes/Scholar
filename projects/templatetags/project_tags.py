import string
import re
from django import template

register = template.Library()
@register.filter
def is_common_skill(skill, project):
    required_ids = [s.id for s in project.skills_required.all()]
    return skill.id in required_ids

@register.filter
def split(value, delimiter=","):
    """Splits the string by the given delimiter."""
    return value.split(delimiter)

@register.filter
def skill_match(project, user):
    """
    Returns the match percentage for the given project and user.
    """
    try:
        return project.get_skill_match(user)
    except Exception:
        return 0

@register.filter
def skill_in_profile(skill, user):
    """
    Returns True if 'skill' (case-insensitive) is in the user's skill list,
    ignoring trailing punctuation like commas or periods.
    """
    if not user.is_authenticated or not hasattr(user, 'profile'):
        return False

    # Remove common punctuation from the start/end of the skill
    skill_clean = skill.strip(string.punctuation).strip().lower()

    # Convert the user's skill names to lowercase, also stripping punctuation if needed
    user_skills_lower = []
    for s in user.profile.skills.all():
        s_clean = s.name.strip(string.punctuation).strip().lower()
        user_skills_lower.append(s_clean)

    return skill_clean in user_skills_lower

@register.filter
def other_participant(room, user):
    """Return the other participant in a 1-on-1 chat."""
    return room.participants.exclude(id=user.id).first()

@register.filter
def skill_in_profile(skill, user):
    if not user.is_authenticated or not hasattr(user, 'profile'):
        return False

    skill_name = skill.name  # skill is a Skill object
    skill_clean = skill_name.strip(string.punctuation).strip().lower()

    user_skills_lower = []
    for s in user.profile.skills.all():
        s_clean = s.name.strip(string.punctuation).strip().lower()
        user_skills_lower.append(s_clean)

    return skill_clean in user_skills_lower



def get_skill_match(self, user):
    if not user.is_authenticated or not hasattr(user, 'profile'):
        return 0
    required_skills = {skill.name.lower() for skill in self.skills_required.all()}
    if not required_skills:
        return 0  # If no required skills, set match to 0 instead of 100.

    user_skills = {skill.name.lower() for skill in user.profile.skills.all()}
    if not user_skills:
        return 0
    match_count = len(required_skills & user_skills)
    return round((match_count / len(required_skills)) * 100)

from projects.models import Skill

@register.filter
def get_skill(skill_id):
    try:
        return Skill.objects.get(id=skill_id)
    except Skill.DoesNotExist:
        return None





