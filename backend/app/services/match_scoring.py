"""Pure scoring helpers for talent matching (no database, no model).

Each candidate gets four component scores in [0, 1]:

semantic      how close the employee's best resume chunks are to the requirement
skill         how relevant the employee's recorded skills are, weighted by proficiency
experience    years of experience in the most relevant skills (absolute, capped)
availability  AVAILABLE > PARTIALLY_AVAILABLE > UNAVAILABLE

``semantic`` and ``skill`` are min-max normalised across the candidates being
compared, because raw cosine similarities sit in a narrow band that differs
from one requirement to the next. The default weights are a starting guess
and should be tuned on the labelled evaluation set, not trusted as-is.
"""
import math
import re

PROFICIENCY_WEIGHT = {"BEGINNER": 0.5, "INTERMEDIATE": 0.7, "ADVANCED": 0.9, "EXPERT": 1.0}
AVAILABILITY_SCORE = {"AVAILABLE": 1.0, "PARTIALLY_AVAILABLE": 0.5, "UNAVAILABLE": 0.0}
EXPERIENCE_CAP_YEARS = 8.0
TOP_SKILLS = 3


def dot(a: list[float], b: list[float]) -> float:
    """Cosine similarity for L2-normalised vectors."""
    return sum(x * y for x, y in zip(a, b))


def mentions_skill(requirement: str, skill_name: str) -> bool:
    """True if the skill name appears as a whole word/phrase in the requirement text."""
    pattern = r"(?<![A-Za-z0-9])" + re.escape(skill_name) + r"(?![A-Za-z0-9])"
    return re.search(pattern, requirement, flags=re.IGNORECASE) is not None


def skill_relevance(requirement: str, skill_name: str, similarity: float) -> float:
    """Explicit mention counts as fully relevant; otherwise use semantic similarity (>= 0)."""
    if mentions_skill(requirement, skill_name):
        return 1.0
    return max(0.0, similarity)


def semantic_raw(similarities: list[float]) -> float:
    """Blend of the best chunk and the mean of the top three: 0.6 * max + 0.4 * mean(top3)."""
    if not similarities:
        return 0.0
    top = sorted(similarities, reverse=True)[:3]
    return 0.6 * top[0] + 0.4 * (sum(top) / len(top))


def skill_scores(skills: list[tuple[str, str, float, float]]) -> tuple[float, float, list[int]]:
    """skills = (name, proficiency, years, relevance).

    Returns (skill_raw, experience_score, indices of the top skills used).
    Top skills are chosen by relevance * proficiency weight.
    """
    if not skills:
        return 0.0, 0.0, []
    weighted = [(rel * PROFICIENCY_WEIGHT.get(prof, 0.7), i) for i, (_, prof, _, rel) in enumerate(skills)]
    weighted.sort(reverse=True)
    top = weighted[:TOP_SKILLS]
    skill_raw = sum(w for w, _ in top) / len(top)
    experience = sum(min(skills[i][2] / EXPERIENCE_CAP_YEARS, 1.0) for _, i in top) / len(top)
    return skill_raw, experience, [i for _, i in top]


def min_max(values: dict) -> dict:
    """Scale values to [0, 1]. If all values are equal, everyone gets 1.0 (or 0.0 if they are all 0)."""
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if math.isclose(hi, lo):
        return {k: (1.0 if hi > 0 else 0.0) for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def combine(semantic: float, skill: float, experience: float, availability: float,
            weights: tuple[float, float, float, float]) -> float:
    total = sum(weights)
    if total <= 0:
        raise ValueError("At least one weight must be greater than zero")
    parts = (semantic, skill, experience, availability)
    return sum(w * p for w, p in zip(weights, parts)) / total
