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

def recommend_projects_for_user(user, top_n=5):
    """
    Recommend projects for the given user.
    Returns the top N recommended projects with an attached FAISS matching score.
    """
    projects = Project.objects.filter(is_active=True)
    projects_list = list(projects)
    if not projects_list:
        return []
    ordered_ids, faiss_scores = rank_projects_with_faiss(projects_list, user)
    top_ids = ordered_ids[:top_n]
    recommended_projects = Project.objects.filter(id__in=top_ids)
    # Preserve the FAISS ordering and attach the score to each project.
    recommended_projects = sorted(recommended_projects, key=lambda p: top_ids.index(p.id))
    for project in recommended_projects:
        project.faiss_score = faiss_scores.get(project.id, 0)
    return recommended_projects
