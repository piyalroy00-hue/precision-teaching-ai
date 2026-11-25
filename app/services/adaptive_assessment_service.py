"""Adaptive question selection and BKT-integrated practice workflow."""
from sqlalchemy.orm import Session

from app.ai.difficulty import recommended_difficulty
from app.config.settings import DIFFICULTY_ORDER
from app.models import Assessment, Question, Response
from app.services.assessment_service import start_assessment, submit_response
from app.services.knowledge_service import get_or_create_knowledge_state


def choose_adaptive_question(session: Session, student_id: int, topic_id: int, difficulty: str) -> Question | None:
    """Prefer unattempted questions at the target difficulty, then nearest new ones."""
    attempted_ids = {
        question_id for (question_id,) in session.query(Response.question_id).filter_by(student_id=student_id)
    }
    candidates = session.query(Question).filter_by(topic_id=topic_id).all()
    unseen = [question for question in candidates if question.id not in attempted_ids]
    pool = unseen or candidates
    if not pool:
        return None
    target_level = DIFFICULTY_ORDER[difficulty]
    return min(
        pool,
        key=lambda question: (abs(DIFFICULTY_ORDER.get(question.difficulty, 2) - target_level), question.id),
    )


def start_adaptive_assessment(session: Session, student_id: int, subject_id: int) -> Assessment:
    return start_assessment(session, student_id, subject_id, assessment_type="adaptive")


def current_adaptive_difficulty(session: Session, student_id: int, topic_id: int) -> str:
    state = get_or_create_knowledge_state(session, student_id, topic_id)
    starting_difficulty = "Easy" if state.mastery_probability < 0.40 else "Medium" if state.mastery_probability < 0.80 else "Hard"
    recent = (
        session.query(Response.is_correct)
        .join(Question)
        .filter(Response.student_id == student_id, Question.topic_id == topic_id)
        .order_by(Response.submitted_at.desc())
        .limit(5)
        .all()
    )
    return recommended_difficulty([result[0] for result in reversed(recent)], starting_difficulty)


def submit_adaptive_response(
    session: Session, assessment_id: int, student_id: int, question_id: int, answer: str, time_taken: float = 0.0
) -> tuple[Response, float, float, str]:
    question = session.get(Question, question_id)
    if question is None:
        raise ValueError(f"Question {question_id} does not exist.")
    state = get_or_create_knowledge_state(session, student_id, question.topic_id)
    previous_mastery = state.mastery_probability
    response = submit_response(session, assessment_id, student_id, question_id, answer, time_taken)
    updated_mastery = get_or_create_knowledge_state(session, student_id, question.topic_id).mastery_probability
    return response, previous_mastery, updated_mastery, current_adaptive_difficulty(session, student_id, question.topic_id)