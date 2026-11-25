"""Persist privacy-scoped student/tutor conversations for the active learning target."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.tutor import TutorContext
from app.models import AIMessage, AISession
from app.services.personalized_tutor_service import PersonalizedTutorService


def start_ai_session(session: Session, student_id: int, topic_id: int) -> AISession:
    ai_session = AISession(student_id=student_id, topic_id=topic_id)
    session.add(ai_session)
    session.flush()
    return ai_session


def respond_to_student(
    session: Session, ai_session_id: int, context: TutorContext, question: str
) -> AIMessage:
    """Record the student message and a target-aware tutor reply for their own session."""
    if not question.strip():
        raise ValueError("A tutor question is required.")
    ai_session = session.get(AISession, ai_session_id)
    if ai_session is None:
        raise ValueError(f"AI session {ai_session_id} does not exist.")
    session.add(AIMessage(session_id=ai_session.id, role="student", message=question.strip()))
    instruction = PersonalizedTutorService().generate(context)
    reply = AIMessage(
        session_id=ai_session.id,
        role="tutor",
        message=f"{instruction.explanation}\n\nHint: {instruction.hint}",
    )
    session.add(reply)
    session.flush()
    return reply


def end_ai_session(session: Session, ai_session_id: int) -> None:
    ai_session = session.get(AISession, ai_session_id)
    if ai_session is not None:
        ai_session.ended_at = datetime.now(timezone.utc)
        session.flush()