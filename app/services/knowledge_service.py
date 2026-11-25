"""Persist and query BKT-based knowledge states for a student."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.bkt import BKTModel, mastery_level
from app.models import KnowledgeState, MasterySnapshot, Topic


def get_or_create_knowledge_state(session: Session, student_id: int, topic_id: int) -> KnowledgeState:
    state = (
        session.query(KnowledgeState)
        .filter_by(student_id=student_id, topic_id=topic_id)
        .one_or_none()
    )
    if state is None:
        model = BKTModel()
        probability = model.initial_mastery()
        state = KnowledgeState(
            student_id=student_id,
            topic_id=topic_id,
            mastery_probability=probability,
            mastery_level=mastery_level(probability),
        )
        session.add(state)
        session.flush()
    return state


def update_knowledge_state(session: Session, student_id: int, topic_id: int, is_correct: bool) -> KnowledgeState:
    state = get_or_create_knowledge_state(session, student_id, topic_id)
    model = BKTModel()
    new_probability = model.update(state.mastery_probability, is_correct)
    state.mastery_probability = new_probability
    state.mastery_level = mastery_level(new_probability)
    state.last_updated = datetime.now(timezone.utc)
    session.add(MasterySnapshot(
        student_id=student_id, topic_id=topic_id, mastery_probability=new_probability
    ))
    session.flush()
    return state


def get_topic_mastery_report(session: Session, student_id: int) -> list[dict]:
    states = (
        session.query(KnowledgeState)
        .filter_by(student_id=student_id)
        .join(Topic)
        .order_by(Topic.id)
        .all()
    )
    return [
        {
            "topic_id": s.topic_id,
            "topic": s.topic.name,
            "mastery_probability": s.mastery_probability,
            "mastery_level": s.mastery_level,
        }
        for s in states
    ]


def classify_concepts(session: Session, student_id: int) -> dict[str, list[str]]:
    report = get_topic_mastery_report(session, student_id)
    return {
        "strong": [r["topic"] for r in report if r["mastery_level"] in ("Proficient", "Mastered")],
        "developing": [r["topic"] for r in report if r["mastery_level"] == "Developing"],
        "weak": [r["topic"] for r in report if r["mastery_level"] == "Beginner"],
    }
