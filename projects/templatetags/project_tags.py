import string

from django import template

register = template.Library()
@register.filter
def is_common_skill(skill, project):
    required_ids = [s.id for s in project.skills_required.all()]
    return skill.id in required_ids


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


