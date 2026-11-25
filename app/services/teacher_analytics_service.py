"""Aggregated instructor analytics; private tutor messages are deliberately excluded."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.seed import leaf_topic_ids
from app.models import KnowledgeState, LearningSession, Response, Topic, User


def class_overview(session: Session) -> dict:
    students = session.query(User).filter_by(role="student").count()
    leaf_ids = leaf_topic_ids(session)
    average_mastery = (
        session.query(func.avg(KnowledgeState.mastery_probability))
        .filter(KnowledgeState.topic_id.in_(leaf_ids))
        .scalar()
        or 0.0
    )
    intervention_count = (
        session.query(KnowledgeState.student_id)
        .filter(
            KnowledgeState.topic_id.in_(leaf_ids),
            KnowledgeState.mastery_probability < 0.40,
        )
        .distinct()
        .count()
    )
    topic_rows = (
        session.query(Topic.name, func.avg(KnowledgeState.mastery_probability))
        .join(KnowledgeState)
        .filter(Topic.id.in_(leaf_ids))
        .group_by(Topic.id)
        .order_by(Topic.name)
        .all()
    )
    return {
        "student_count": students,
        "average_mastery": average_mastery,
        "students_requiring_intervention": intervention_count,
        "topic_mastery": [{"topic": name, "mastery": mastery} for name, mastery in topic_rows],
    }


def student_analytics(session: Session, student_id: int) -> dict:
    leaf_ids = leaf_topic_ids(session)
    states = (
        session.query(KnowledgeState)
        .filter_by(student_id=student_id)
        .filter(KnowledgeState.topic_id.in_(leaf_ids))
        .join(Topic)
        .all()
    )
    sessions = session.query(LearningSession).filter_by(student_id=student_id).all()
    return {
        "topic_mastery": [{"topic": state.topic.name, "mastery": state.mastery_probability} for state in states],
        "completed_sessions": sum(item.completed_at is not None for item in sessions),
        "learning_minutes": sum(item.resource.estimated_minutes for item in sessions if item.completed_at),
    }


def all_student_performance(session: Session) -> list[dict]:
    """Return a privacy-safe performance summary for each student account."""
    students = session.query(User).filter_by(role="student").order_by(User.student_code).all()
    performance = []
    leaf_ids = leaf_topic_ids(session)
    for student in students:
        states = (
            session.query(KnowledgeState)
            .filter_by(student_id=student.id)
            .filter(KnowledgeState.topic_id.in_(leaf_ids))
            .all()
        )
        responses = session.query(Response).filter_by(student_id=student.id).all()
        sessions = session.query(LearningSession).filter_by(student_id=student.id).all()
        average_mastery = (
            sum(state.mastery_probability for state in states) / len(states) if states else 0.0
        )
        accuracy = (
            sum(response.is_correct for response in responses) / len(responses) if responses else 0.0
        )
        performance.append({
            "id": student.id,
            "code": student.student_code,
            "name": student.name,
            "average_mastery": average_mastery,
            "attempts": len(responses),
            "accuracy": accuracy,
            "completed_sessions": sum(item.completed_at is not None for item in sessions),
            "requires_intervention": any(state.mastery_probability < 0.40 for state in states),
        })
    return performance