import string

from django import template

register = template.Library()

@register.filter
def skill_match(project, user):
    return project.get_skill_match(user)

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

