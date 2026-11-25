"""Create and persist validated, deterministic development practice content."""
import json

from sqlalchemy.orm import Session

from app.ai.content_validator import GeneratedPracticeQuestion, validate_practice_question
from app.ai.prompt_generator import PROMPT_VERSION
from app.ai.tutor import TutorContext
from app.models import GeneratedContent


def generate_practice_question(context: TutorContext) -> GeneratedPracticeQuestion:
    """Produce a clearly synthetic fallback question until an LLM adapter is configured."""
    topic = context.subtopic or context.topic
    question = GeneratedPracticeQuestion(
        question=f"Which statement best supports this objective: {context.learning_objective}?",
        options=(
            f"Apply {topic} step by step.",
            "Skip directly to an unrelated advanced concept.",
            "Ignore the result of the program.",
        ),
        correct_answer=f"Apply {topic} step by step.",
        explanation=f"The correct choice directly applies the {context.difficulty.lower()} {topic} objective.",
        difficulty=context.difficulty,
    )
    validation = validate_practice_question(question)
    if not validation.is_valid:
        raise ValueError(validation.message)
    return question


def _serialize(question: GeneratedPracticeQuestion) -> str:
    return json.dumps(question.__dict__, sort_keys=True)


def save_generated_practice(
    session: Session, student_id: int, topic_id: int, question: GeneratedPracticeQuestion
) -> GeneratedContent:
    """Store only validated generated content and its prompt version for audit/review."""
    validation = validate_practice_question(question)
    if not validation.is_valid:
        raise ValueError(validation.message)
    record = GeneratedContent(
        student_id=student_id,
        topic_id=topic_id,
        content_type="practice_question",
        prompt_version=PROMPT_VERSION,
        generated_content=_serialize(question),
        validation_status="validated",
    )
    session.add(record)
    session.flush()
    return record


def get_or_create_generated_practice(
    session: Session, student_id: int, topic_id: int, question: GeneratedPracticeQuestion
) -> GeneratedContent:
    """Reuse an identical audit record instead of inserting on every page view."""
    payload = _serialize(question)
    existing = (
        session.query(GeneratedContent)
        .filter_by(
            student_id=student_id,
            topic_id=topic_id,
            content_type="practice_question",
            prompt_version=PROMPT_VERSION,
            generated_content=payload,
        )
        .order_by(GeneratedContent.id)
        .first()
    )
    if existing is not None:
        return existing
    return save_generated_practice(session, student_id, topic_id, question)
