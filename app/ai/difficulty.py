"""Stable adaptive difficulty selection based on a recent response window."""
from app.config.settings import ADAPTIVE_WINDOW_SIZE, DIFFICULTY_ORDER


def recommended_difficulty(recent_correctness: list[bool], current_difficulty: str = "Medium") -> str:
    """Move at most one level after a full response window to avoid oscillation."""
    current_level = DIFFICULTY_ORDER.get(current_difficulty, 2)
    if len(recent_correctness) < ADAPTIVE_WINDOW_SIZE:
        return current_difficulty

    accuracy = sum(recent_correctness[-ADAPTIVE_WINDOW_SIZE:]) / ADAPTIVE_WINDOW_SIZE
    if accuracy >= 0.80:
        current_level += 1
    elif accuracy <= 0.40:
        current_level -= 1

    current_level = min(max(current_level, 1), 3)
    return next(name for name, level in DIFFICULTY_ORDER.items() if level == current_level)