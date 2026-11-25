"""Learning-resource session lifecycle operations."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import LearningResource, LearningSession, Recommendation


def start_learning_session(session: Session, student_id: int, resource_id: int) -> LearningSession:
    resource = session.get(LearningResource, resource_id)
    if resource is None:
        raise ValueError(f"Learning resource {resource_id} does not exist.")
    learning_session = LearningSession(
        student_id=student_id, topic_id=resource.topic_id, resource_id=resource.id
    )
    session.add(learning_session)
    session.flush()
    return learning_session


def complete_learning_session(session: Session, learning_session_id: int) -> LearningSession:
    learning_session = session.get(LearningSession, learning_session_id)
    if learning_session is None:
        raise ValueError(f"Learning session {learning_session_id} does not exist.")
    learning_session.completion_percentage = 100.0
    learning_session.completed_at = datetime.now(timezone.utc)
    recommendation = (
        session.query(Recommendation)
        .filter_by(
            student_id=learning_session.student_id,
            topic_id=learning_session.topic_id,
            resource_id=learning_session.resource_id,
        )
        .order_by(Recommendation.recommended_at.desc())
        .first()
    )
    if recommendation is not None:
        recommendation.completed = True
    session.flush()
    return learning_session