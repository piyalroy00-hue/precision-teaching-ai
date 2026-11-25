"""Deterministic synthetic learning resources used by the Phase 2 demo."""
from sqlalchemy.orm import Session

from app.models import LearningResource, Topic

RESOURCE_TYPES = ("explanation", "example", "worked_example", "practice", "summary", "exercise")


def seed_learning_resources(session: Session) -> None:
    """Create clearly labelled synthetic resources once for each curriculum topic."""
    if session.query(LearningResource.id).first() is not None:
        return

    topics = session.query(Topic).order_by(Topic.id).all()
    for topic in topics:
        for index, resource_type in enumerate(RESOURCE_TYPES):
            difficulty = ("Easy", "Medium", "Hard")[index % 3]
            objective = f"Build confidence applying {topic.name} in Python."
            session.add(
                LearningResource(
                    topic_id=topic.id,
                    title=f"{topic.name}: {resource_type.replace('_', ' ').title()}",
                    content=(
                        f"Synthetic Phase 2 learning material. {objective} "
                        f"Study this {difficulty.lower()} {resource_type.replace('_', ' ')} "
                        "and then complete the adaptive practice activity."
                    ),
                    resource_type=resource_type,
                    difficulty=difficulty,
                    estimated_minutes=10 + (index * 5),
                )
            )
    session.flush()