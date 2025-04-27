import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from projects.models import Project
from users.models import Profile

def build_text_profile(project):
    """
    Build a textual profile for a project by combining its skills,
    mission, objectives, description, and categories.
    """
    skills_text = " ".join([skill.name for skill in project.skills_required.all()])
    mission_text = project.project_mission or ""
    objectives_text = project.project_objectives or ""
    description_text = project.description or ""
    categories_text = " ".join([cat.name for cat in project.category.all()])
    return " ".join([skills_text, mission_text, objectives_text, description_text, categories_text]).strip()

def rank_projects_with_faiss(projects, user):
    """
    Given a list of project objects and a user, compute a ranking of project IDs
    based on the similarity between each project's text profile and the user's profile.
    Returns:
        A tuple: (ordered_project_ids, faiss_scores)
            ordered_project_ids: list of project IDs ordered from most similar (lowest L2 distance) to least.
            faiss_scores: dictionary mapping project ID to a computed similarity percentage.
    """
    project_texts = []
    project_ids = []
    for project in projects:
        text = build_text_profile(project)
        project_texts.append(text)
        project_ids.append(project.id)
    if not project_texts:
        return [], {}
    # Create TF-IDF vectors for all project profiles.
    vectorizer = TfidfVectorizer()
    project_vectors = vectorizer.fit_transform(project_texts).toarray().astype('float32')
    d = project_vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(project_vectors)
    # Build the user's profile using their skills, bio, and categories.
    user_skills_text = " ".join([skill.name for skill in user.profile.skills.all()])
    bio_text = user.profile.bio or ""
    user_categories_text = " ".join([cat.name for cat in user.profile.categories.all()])
    user_profile_text = " ".join([user_skills_text, bio_text, user_categories_text]).strip()
    user_vector = vectorizer.transform([user_profile_text]).toarray().astype('float32')
    total_projects = len(project_ids)
    distances, indices = index.search(user_vector, total_projects)
    # Compute a similarity percentage from each L2 distance.
    faiss_scores = {}
    for rank, idx in enumerate(indices[0]):
        distance = distances[0][rank]
        # Convert L2 distance into a similarity score (higher is better)
        similarity = (1 / (1 + distance)) * 100
        faiss_scores[project_ids[idx]] = round(similarity, 2)
    ordered_ids = [project_ids[i] for i in indices[0]]
    return ordered_ids, faiss_scores

def recommend_projects_for_user(user):
    """
    Recommend all active projects for the given user, sorted by similarity.
    Each project will have an attribute 'faiss_score' representing the matching percentage.
    """
    projects = Project.objects.filter(is_active=True)
    projects_list = list(projects)
    if not projects_list:
        return []
    ordered_ids, faiss_scores = rank_projects_with_faiss(projects_list, user)
    recommended_projects = Project.objects.filter(id__in=ordered_ids)
    # Preserve FAISS ordering
    recommended_projects = sorted(recommended_projects, key=lambda p: ordered_ids.index(p.id))
    for project in recommended_projects:
        project.faiss_score = faiss_scores.get(project.id, 0)
    return recommended_projects




#reserse, recommend users to project

def rank_users_with_faiss(users, project):
    """
    Given a list of candidate users and a project,
    compute a ranking of user IDs based on the similarity between each user's profile text
    (constructed from their skills, bio, and categories) and the project's text profile.
    Returns:
        A tuple: (ordered_user_ids, faiss_scores)
            ordered_user_ids: list of user IDs ordered from most similar (highest similarity) to least.
            faiss_scores: dictionary mapping user ID to a computed similarity percentage.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    user_texts = []
    user_ids = []
    for user in users:
        # Build user profile text
        skills_text = " ".join([skill.name for skill in user.profile.skills.all()])
        bio_text = user.profile.bio or ""
        categories_text = " ".join([cat.name for cat in user.profile.categories.all()])
        text = " ".join([skills_text, bio_text, categories_text]).strip()
        user_texts.append(text)
        user_ids.append(user.id)
    if not user_texts:
        return [], {}
    # Vectorize the user texts
    vectorizer = TfidfVectorizer()
    user_vectors = vectorizer.fit_transform(user_texts).toarray().astype('float32')
    d = user_vectors.shape[1]
    import faiss
    index = faiss.IndexFlatL2(d)
    index.add(user_vectors)
    # Build the project profile vector using your existing build_text_profile function
    project_text = build_text_profile(project)
    project_vector = vectorizer.transform([project_text]).toarray().astype('float32')
    total_users = len(user_ids)
    distances, indices = index.search(project_vector, total_users)
    # Convert L2 distances to similarity percentages (higher is better)
    faiss_scores = {}
    for rank, idx in enumerate(indices[0]):
        distance = distances[0][rank]
        similarity = (1 / (1 + distance)) * 100
        faiss_scores[user_ids[idx]] = round(similarity, 2)
    ordered_ids = [user_ids[i] for i in indices[0]]
    return ordered_ids, faiss_scores

def recommend_users_for_project(project, top_n=5):
    """
    Recommend candidate users for the given project.
    Excludes the project owner and returns the top N users sorted by a FAISS-based match score.
    Each returned user will have an attribute 'faiss_score' with the computed match percentage.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # Consider active users excluding the project owner
    candidates = User.objects.filter(is_active=True).exclude(id=project.owner.id)
    ordered_ids, faiss_scores = rank_users_with_faiss(candidates, project)
    top_ids = ordered_ids[:top_n]
    recommended_users = User.objects.filter(id__in=top_ids)
    # Preserve the FAISS ordering
    recommended_users = sorted(recommended_users, key=lambda u: top_ids.index(u.id))
    for user in recommended_users:
        user.faiss_score = faiss_scores.get(user.id, 0)
    return recommended_users

