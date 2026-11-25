"""Diagnostic assessment workflow: fixed question set, response recording,
scoring, and BKT-driven knowledge state updates."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Assessment, Question, Response, Topic
from app.services.knowledge_service import update_knowledge_state

DIFFICULTY_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


def get_fixed_diagnostic_questions(session: Session, subject_id: int) -> list[Question]:
    """The Phase-1 diagnostic uses a fixed (non-adaptive) question set: the
    hand-authored base bank ('generated' source), covering every topic and
    difficulty level. Adaptive selection is deferred to Phase 2."""
    questions = (
        session.query(Question)
        .join(Topic, Question.topic_id == Topic.id)
        .filter(Topic.subject_id == subject_id, Question.source == "generated")
        .all()
    )
    return sorted(questions, key=lambda q: (q.topic_id, DIFFICULTY_ORDER.get(q.difficulty, 99), q.id))


def start_assessment(session: Session, student_id: int, subject_id: int, assessment_type: str = "diagnostic") -> Assessment:
    assessment = Assessment(student_id=student_id, subject_id=subject_id, assessment_type=assessment_type)
    session.add(assessment)
    session.commit()
    return assessment


def submit_response(
    session: Session,
    assessment_id: int,
    student_id: int,
    question_id: int,
    answer: str,
    time_taken: float = 0.0,
) -> Response:
    question = session.get(Question, question_id)
    if question is None:
        raise ValueError(f"Question {question_id} does not exist.")

    is_correct = answer.strip() == question.correct_answer.strip()
    score = question.marks if is_correct else 0.0
    attempt_number = (
        session.query(Response).filter_by(student_id=student_id, question_id=question_id).count() + 1
    )

    response = Response(
        assessment_id=assessment_id,
        student_id=student_id,
        question_id=question_id,
        answer=answer,
        is_correct=is_correct,
        score=score,
        time_taken=time_taken,
        attempt_number=attempt_number,
    )
    session.add(response)
    session.flush()

    update_knowledge_state(session, student_id=student_id, topic_id=question.topic_id, is_correct=is_correct)
    session.commit()
    return response


def complete_assessment(session: Session, assessment_id: int) -> Assessment:
    assessment = session.get(Assessment, assessment_id)
    if assessment is None:
        raise ValueError(f"Assessment {assessment_id} does not exist.")

    responses = assessment.responses
    total_score = sum(r.score for r in responses)
    total_possible = sum(r.question.marks for r in responses)

    assessment.total_score = total_score
    assessment.percentage = (total_score / total_possible * 100) if total_possible > 0 else 0.0
    assessment.completed_at = datetime.now(timezone.utc)
    session.commit()
    return assessment
