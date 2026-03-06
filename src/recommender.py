"""
Component 3: Skill Similarity & Recommender (Capstone 3 – ML methodology).
TF-IDF + cosine similarity for occupation/skill similarity; ranks transitions and skill gaps.
This project does not implement Capstone 4 (deep learning); similarity is framed as ML.
"""
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _occupation_text_for_similarity(o: dict) -> str:
    """Single text for TF-IDF/similarity: title, skills, abilities, knowledge, work_activities, interests."""
    parts = [
        o.get("title") or "",
        o.get("skills") or "",
        o.get("abilities") or "",
        o.get("knowledge") or "",
        o.get("work_activities") or "",
        o.get("interests") or "",
    ]
    return " ".join(p.strip() for p in parts if p).strip() or (o.get("id") or "")


def build_skill_similarity_matrix(occupations: list[dict]) -> tuple[np.ndarray, TfidfVectorizer]:
    """Build occupation x occupation similarity via TF-IDF on title, skills, abilities, knowledge,
    work_activities, and interests (all optional). Uses all available text so recommendations
    benefit from the expanded O*NET schema."""
    texts = [_occupation_text_for_similarity(o) for o in occupations]
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)
    sim = cosine_similarity(X, X)
    return np.clip(sim, 0, 1), vectorizer


def compute_similarity_of_text_to_occupations(
    text: str,
    occupations: list[dict],
    vectorizer: TfidfVectorizer,
) -> np.ndarray:
    """
    Compute TF-IDF cosine similarity of a single text (e.g. user-augmented profile) to every
    occupation. Use this to replace the current occupation's row in the skill matrix so
    recommendations reflect the user's selected skills, abilities, knowledge, interests.
    Returns 1d array of shape (len(occupations),) with values in [0, 1].
    """
    if not text.strip():
        # Fallback: use zero similarity so we don't break
        return np.zeros(len(occupations))
    occ_texts = [_occupation_text_for_similarity(o) for o in occupations]
    X_occ = vectorizer.transform(occ_texts)
    X_query = vectorizer.transform([text])
    sim = cosine_similarity(X_query, X_occ).ravel()
    return np.clip(sim, 0, 1)


def _get_gaps(current_str: Optional[str], target_str: Optional[str]) -> list[str]:
    """Return list of items in target (comma-separated) that are not in current."""
    curr = set(s.strip() for s in (current_str or "").lower().split(",") if s.strip())
    tgt = set(s.strip() for s in (target_str or "").lower().split(",") if s.strip())
    return sorted(tgt - curr)


def get_skill_gaps(current_skills: Optional[str], target_skills: Optional[str]) -> list[str]:
    """Return list of skills in target that are not in current (simplified)."""
    return _get_gaps(current_skills, target_skills)


def recommend_transitions(
    current_occ: dict,
    occupations: list[dict],
    skill_matrix: np.ndarray,
    stats: dict,
    top_k: int = 5,
) -> list[dict]:
    """
    Rank candidate transitions by combined score: profile overlap (TF-IDF), growth, salary.
    Returns top_k with required skill gaps.
    """
    curr_id = current_occ["id"]
    curr_idx = next(i for i, o in enumerate(occupations) if o["id"] == curr_id)
    candidates = []
    for j, target in enumerate(occupations):
        if target["id"] == curr_id:
            continue
        overlap = float(skill_matrix[curr_idx, j])
        growth = (stats.get(target["id"], {}).get("growth_score") or 0) / 100
        salary = target.get("median_salary", 0) or 0
        salary_norm = min(salary / 150000, 1.0)  # cap so high salary doesn't dominate over skill fit
        score = 0.8 * overlap + 0.1 * growth + 0.1 * salary_norm
        skill_gaps = get_skill_gaps(current_occ.get("skills"), target.get("skills"))
        knowledge_gaps = _get_gaps(current_occ.get("knowledge"), target.get("knowledge"))
        ability_gaps = _get_gaps(current_occ.get("abilities"), target.get("abilities"))
        interest_gaps = _get_gaps(current_occ.get("interests"), target.get("interests"))
        salary_current = current_occ.get("median_salary", 0) or 0
        salary_delta = (salary or 0) - salary_current
        rec = {
            "target": target,
            "skill_overlap": overlap,
            "skill_gaps": skill_gaps,
            "knowledge_gaps": knowledge_gaps,
            "ability_gaps": ability_gaps,
            "interest_gaps": interest_gaps,
            "score": score,
            "growth_pct": target.get("growth_pct"),
            "median_salary": salary,
            "salary_delta": salary_delta,
        }
        candidates.append(rec)
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:top_k]
