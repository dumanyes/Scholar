# recommendation.py

import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from projects.models import Project
from users.models import Profile

# Global TF–IDF model and FAISS index, built once per process
_GLOBAL_TFIDF = None       # TfidfVectorizer instance
_GLOBAL_IDS = None         # list of project IDs in the TF–IDF corpus
_GLOBAL_VEC = None         # numpy array of their TF–IDF vectors
_GLOBAL_INDEX = None       # faiss.IndexFlatL2 built on _GLOBAL_VEC

def build_text_profile(project):
    """
    Build a textual profile for a project by combining its skills,
    mission, objectives, description, and categories.
    """
    skills_text      = " ".join([skill.name for skill in project.skills_required.all()])
    mission_text     = project.project_mission or ""
    objectives_text  = project.project_objectives or ""
    description_text = project.description or ""
    categories_text  = " ".join([cat.name for cat in project.category.all()])
    return " ".join([
        skills_text,
        mission_text,
        objectives_text,
        description_text,
        categories_text
    ]).strip()

def _init_global_tfidf():
    """
    Initialize the global TF–IDF vectorizer, project vectors, and FAISS index
    on all active projects.
    """
    global _GLOBAL_TFIDF, _GLOBAL_IDS, _GLOBAL_VEC, _GLOBAL_INDEX

    if _GLOBAL_TFIDF is None:
        # 1) load all active projects
        projects = list(Project.objects.filter(is_active=True))
        texts    = [build_text_profile(p) for p in projects]
        ids      = [p.id for p in projects]

        # 2) fit TF–IDF on every project description
        vec    = TfidfVectorizer()
        matrix = vec.fit_transform(texts).toarray().astype('float32')

        # 3) build a FAISS L2 index
        d      = matrix.shape[1]
        index  = faiss.IndexFlatL2(d)
        index.add(matrix)

        # store globals
        _GLOBAL_TFIDF = vec
        _GLOBAL_IDS   = ids
        _GLOBAL_VEC   = matrix
        _GLOBAL_INDEX = index

def rank_projects_with_faiss(projects, user):
    """
    Rank the given list of project objects by FAISS-based similarity to the user.
    Uses a global TF–IDF model trained on all active projects so that scores
    are consistent across Marketplace and Favorites.
    Returns:
        (ordered_project_ids, faiss_scores)
    """
    _init_global_tfidf()

    # build the user profile vector
    user_skills_text      = " ".join([skill.name for skill in user.profile.skills.all()])
    bio_text              = user.profile.bio or ""
    user_categories_text  = " ".join([cat.name for cat in user.profile.categories.all()])
    user_profile_text     = " ".join([
        user_skills_text,
        bio_text,
        user_categories_text
    ]).strip()

    user_vec = _GLOBAL_TFIDF.transform([user_profile_text]) \
                             .toarray() \
                             .astype('float32')

    # search over the full index
    distances, indices = _GLOBAL_INDEX.search(user_vec, len(_GLOBAL_IDS))

    # convert distances → similarity % and build a dict
    faiss_scores = {}
    for rank, idx in enumerate(indices[0]):
        dist       = distances[0][rank]
        similarity = (1 / (1 + dist)) * 100
        pid        = _GLOBAL_IDS[idx]
        faiss_scores[pid] = round(similarity, 2)

    # now filter and order only the projects passed in
    project_id_set = {p.id for p in projects}
    ordered_ids    = [pid for pid in _GLOBAL_IDS if pid in project_id_set]

    return ordered_ids, faiss_scores

def recommend_projects_for_user(user):
    """
    Recommend all active projects for the given user, sorted by FAISS similarity.
    Each returned Project instance gets a .faiss_score attribute.
    """
    all_active = list(Project.objects.filter(is_active=True))
    if not all_active:
        return []

    ordered_ids, faiss_scores = rank_projects_with_faiss(all_active, user)

    # fetch them in bulk and preserve the ranking
    projs = Project.objects.filter(id__in=ordered_ids)
    projs = sorted(projs, key=lambda p: ordered_ids.index(p.id))

    for p in projs:
        p.faiss_score = faiss_scores.get(p.id, 0)

    return projs

# --- user ranking reversed: unchanged from before ---

def rank_users_with_faiss(users, project):
    """
    Rank candidate users by FAISS similarity to the given project.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    # build user texts
    user_texts, user_ids = [], []
    for u in users:
        skills_text      = " ".join([s.name for s in u.profile.skills.all()])
        bio_text         = u.profile.bio or ""
        categories_text  = " ".join([c.name for c in u.profile.categories.all()])
        txt = " ".join([skills_text, bio_text, categories_text]).strip()
        user_texts.append(txt)
        user_ids.append(u.id)

    if not user_texts:
        return [], {}

    vec         = TfidfVectorizer()
    user_matrix = vec.fit_transform(user_texts).toarray().astype('float32')

    d     = user_matrix.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(user_matrix)

    proj_text   = build_text_profile(project)
    proj_vector = vec.transform([proj_text]).toarray().astype('float32')

    distances, indices = index.search(proj_vector, len(user_ids))

    faiss_scores = {}
    for rank, idx in enumerate(indices[0]):
        dist       = distances[0][rank]
        similarity = (1 / (1 + dist)) * 100
        uid        = user_ids[idx]
        faiss_scores[uid] = round(similarity, 2)

    ordered = [user_ids[i] for i in indices[0]]
    return ordered, faiss_scores

def recommend_users_for_project(project, top_n=5):
    """
    Wrap-up: returns top-N users for the project, each with a .faiss_score.
    """
    from django.contrib.auth import get_user_model
    User       = get_user_model()
    candidates = User.objects.filter(is_active=True).exclude(id=project.owner.id)

    ordered_ids, faiss_scores = rank_users_with_faiss(candidates, project)
    top_ids                   = ordered_ids[:top_n]

    users = list(User.objects.filter(id__in=top_ids))
    users = sorted(users, key=lambda u: top_ids.index(u.id))

    for u in users:
        u.faiss_score = faiss_scores.get(u.id, 0)

    return users
