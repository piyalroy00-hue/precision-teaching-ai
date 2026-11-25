"""Knowledge-gap classification based on persisted BKT mastery."""
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeGap:
    topic_id: int
    topic_name: str
    mastery: float
    priority: str


def priority_for_mastery(mastery: float) -> str:
    if mastery < 0.40:
        return "High"
    if mastery < 0.70:
        return "Medium"
    if mastery < 0.90:
        return "Low"
    return "None"


def detect_gaps(mastery_report: list[dict]) -> list[KnowledgeGap]:
    """Return non-mastered topics ordered from the most urgent BKT gap."""
    gaps = [
        KnowledgeGap(
            topic_id=item["topic_id"],
            topic_name=item["topic"],
            mastery=item["mastery_probability"],
            priority=priority_for_mastery(item["mastery_probability"]),
        )
        for item in mastery_report
        if item["mastery_probability"] < 0.90
    ]
    return sorted(gaps, key=lambda gap: gap.mastery)