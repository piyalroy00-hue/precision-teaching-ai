"""Central configuration for paths, database, and BKT defaults."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
GENERATED_DATA_DIR = DATA_DIR / "generated"
AUGMENTED_DATA_DIR = DATA_DIR / "augmented"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

DATABASE_PATH = BASE_DIR / "precision_teaching.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Fixed seed so dataset generation/augmentation is reproducible.
RANDOM_SEED = 42

# Standard Bayesian Knowledge Tracing parameters (per-topic overrides allowed later).
BKT_DEFAULTS = {
    "p_init": 0.20,   # P(L0) - probability the student already knows the skill
    "p_transit": 0.15,  # P(T) - probability of learning the skill after an opportunity
    "p_guess": 0.20,   # P(G) - probability of guessing correctly without knowing the skill
    "p_slip": 0.10,    # P(S) - probability of an incorrect answer despite knowing the skill
}

# Mastery probability -> interpreted mastery level bands.
# These are cutoffs, not exact closed intervals: values under 0.40 are Beginner,
# values under 0.70 are Developing, values under 0.90 are Proficient, and
# values at/above 0.90 are Mastered. This keeps the ranges contiguous.
MASTERY_LEVELS = (
    (0.00, 0.39, "Beginner"),
    (0.40, 0.69, "Developing"),
    (0.70, 0.89, "Proficient"),
    (0.90, 1.00, "Mastered"),
)

SUBJECT_NAME = "Python Programming"

# Phase 2 recommendation weights. Gap severity leads because the goal is to
# close meaningful learning gaps; prerequisite readiness, difficulty fit, recent
# performance, and resource novelty make the recommendation actionable.
RECOMMENDATION_WEIGHTS = {
    "knowledge_gap": 0.35,
    "prerequisite_relevance": 0.25,
    "difficulty_match": 0.15,
    "recent_performance": 0.15,
    "resource_freshness": 0.10,
}

ADAPTIVE_WINDOW_SIZE = 5
DIFFICULTY_ORDER = {"Easy": 1, "Medium": 2, "Hard": 3}

# Local content is the safe default. Set AI_TUTOR_PROVIDER=openai and provide
# OPENAI_API_KEY only in the deployment environment to enable external generation.
AI_TUTOR_PROVIDER = os.getenv("AI_TUTOR_PROVIDER", "local").lower()
OPENAI_TUTOR_MODEL = os.getenv("OPENAI_TUTOR_MODEL", "gpt-4o-mini")
