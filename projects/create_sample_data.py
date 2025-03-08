import random
from django.contrib.auth.models import User
from projects.models import (
    Category, Language, RequiredRole, Skill, Project
)
from users.models import Profile


import random
from django.contrib.auth.models import User
from projects.models import (
    Category, Language, RequiredRole, Skill, Project
)
from users.models import Profile

def create_sample_data(num_users=100):

    all_categories = list(Category.objects.all())
    all_languages = list(Language.objects.all())
    all_roles = list(RequiredRole.objects.all())
    all_skills = list(Skill.objects.all())

    # Basic checks
    if not all_skills:
        print("No skills found in the database. Please load skills first.")
        return
    if not all_categories:
        print("No categories found in the database. Please load categories first.")
        return
    if not all_languages:
        print("No languages found in the database. Please load languages first.")
    if not all_roles:
        print("No required roles found in the database. Please load required roles first.")

    for i in range(num_users):
        username = f"user_{i}"
        email = f"user_{i}@example.com"
        # Create or get user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email}
        )
        if created:
            user.set_password("password")
            user.save()

        # Get or create the user's Profile
        profile = user.profile
        profile.bio = f"This is a sample bio for {username}."

        # Assign random skills to the user
        user_skill_count = random.randint(1, 6)  # 1 to 6 skills
        user_skills = random.sample(all_skills, min(user_skill_count, len(all_skills)))
        profile.skills.set(user_skills)
        profile.save()

        # Create 1–3 random projects for this user
        project_count = random.randint(1, 3)
        for j in range(project_count):
            project_title = f"Project_{i}_{j}"
            project_description = (
                f"This is a sample description for {project_title}, "
                f"owned by {username}."
            )

            project = Project.objects.create(
                title=project_title,
                description=project_description,
                project_mission="Sample project mission.",
                project_objectives="Sample project objectives.",
                owner=user
            )

            # Random categories
            cat_count = random.randint(1, 3)
            if all_categories:
                random_categories = random.sample(all_categories, min(cat_count, len(all_categories)))
                project.category.set(random_categories)

            # Random required roles
            role_count = random.randint(0, 3)
            if all_roles and role_count > 0:
                random_roles = random.sample(all_roles, min(role_count, len(all_roles)))
                project.required_roles.set(random_roles)

            # Random languages
            lang_count = random.randint(0, 2)
            if all_languages and lang_count > 0:
                random_langs = random.sample(all_languages, min(lang_count, len(all_languages)))
                project.languages.set(random_langs)

            # Random required skills
            required_skill_count = random.randint(1, 6)
            random_project_skills = random.sample(all_skills, min(required_skill_count, len(all_skills)))
            project.skills_required.set(random_project_skills)

            project.save()

        print(f"Created/updated {username} with {project_count} project(s).")

# Finally, call the function:
create_sample_data(num_users=100)




