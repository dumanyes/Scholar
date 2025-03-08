# projects/recommendation.py
import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from projects.models import Project
from users.models import Profile


def build_text_profile(project):
    """
    Build a textual profile for a project by combining its skills,
    mission, objectives, and description.
    """
    skills_text = " ".join([skill.name for skill in project.skills_required.all()])
    mission_text = project.project_mission or ""
    objectives_text = project.project_objectives or ""
    description_text = project.description or ""
    return " ".join([skills_text, mission_text, objectives_text, description_text]).strip()


def rank_projects_with_faiss(projects, user):
    """
    Given a list of project objects and a user, compute a ranking of project IDs
    based on the similarity between each project's text profile and the user's profile.

    Returns:
        A list of project IDs ordered from most similar (lowest L2 distance) to least.
    """
    project_texts = []
    project_ids = []

    for project in projects:
        text = build_text_profile(project)
        project_texts.append(text)
        project_ids.append(project.id)

    if not project_texts:
        return []

    # Create TF-IDF vectors for all project profiles.
    vectorizer = TfidfVectorizer()
    project_vectors = vectorizer.fit_transform(project_texts).toarray().astype('float32')

    # Build a FAISS index using L2 (Euclidean) distance.
    d = project_vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(project_vectors)

    # Build the user's profile using their skills and bio.
    user_skills_text = " ".join([skill.name for skill in user.profile.skills.all()])
    bio_text = user.profile.bio or ""
    user_profile_text = " ".join([user_skills_text, bio_text]).strip()

    # Transform the user's profile into a TF-IDF vector.
    user_vector = vectorizer.transform([user_profile_text]).toarray().astype('float32')

    # Query the index to get the ranking for all projects.
    total_projects = len(project_ids)
    distances, indices = index.search(user_vector, total_projects)

    # indices[0] contains the positions of projects in order of increasing L2 distance.
    ordered_ids = [project_ids[i] for i in indices[0]]
    return ordered_ids


def recommend_projects_for_user(user, top_n=5):
    """
    Recommend projects for the given user.

    This function fetches all active projects from the database,
    ranks them using FAISS based on similarity to the user's profile,
    and returns the top N recommended projects.
    """
    projects = Project.objects.filter(is_active=True)
    projects_list = list(projects)

    # Get the ordering of project IDs from most similar to least.
    ordered_ids = rank_projects_with_faiss(projects_list, user)

    # Select the top N project IDs.
    top_ids = ordered_ids[:top_n]

    # Retrieve the recommended projects from the database.
    recommended_projects = Project.objects.filter(id__in=top_ids)

    # Preserve the order as determined by FAISS.
    recommended_projects = sorted(recommended_projects, key=lambda p: top_ids.index(p.id))
    return recommended_projects
