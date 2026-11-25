"""Transparent scoring for personalized learning-resource recommendations."""
from dataclasses import dataclass

from app.config.settings import RECOMMENDATION_WEIGHTS


@dataclass(frozen=True)
class RecommendationScore:
    score: float
    priority: str
    reason: str


def score_resource(
    mastery: float,
    prerequisite_relevance: float,
    difficulty_match: float,
    recent_performance: float,
    resource_freshness: float,
) -> RecommendationScore:
    """Score a candidate with normalized [0, 1] learner/context signals."""
    values = {
        "knowledge_gap": 1 - mastery,
        "prerequisite_relevance": prerequisite_relevance,
        "difficulty_match": difficulty_match,
        "recent_performance": 1 - recent_performance,
        "resource_freshness": resource_freshness,
    }
    score = sum(RECOMMENDATION_WEIGHTS[name] * value for name, value in values.items())
    priority = "High" if score >= 0.65 else "Medium" if score >= 0.40 else "Low"
    reason = (
        f"Mastery is {mastery:.0%}; this {priority.lower()}-priority resource "
        "matches the learner's current readiness and prerequisite needs."
    )
    return RecommendationScore(score=score, priority=priority, reason=reason)