from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.ai.tutor import TutorContext
from app.database.db import Base
from app.database.seed import seed_subject_and_topics
from app.models import AIMessage, GeneratedContent, KnowledgeState, User
from app.services.generated_practice_service import generate_practice_question, save_generated_practice
from app.services.teacher_analytics_service import class_overview
from app.services.tutor_conversation_service import respond_to_student, start_ai_session
from ml.evaluation.metrics import calculate_learning_outcome, prediction_metrics


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    topic_id = seed_subject_and_topics(session)["Recursion"]
    student = User(student_code="P3001", name="Student", email="p3@example.test", password_hash="x")
    session.add(student)
    session.flush()
    return session, student, topic_id


def _context() -> TutorContext:
    return TutorContext(
        subject="Python Programming", topic="Recursion", subtopic="Base case",
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Explain why recursion stops.", previous_errors=("Missing a base case",),
    )


def test_validated_practice_is_audited_with_its_prompt_version():
    session, student, topic_id = _session()
    question = generate_practice_question(_context())

    record = save_generated_practice(session, student.id, topic_id, question)

    assert record.validation_status == "validated"
    assert session.query(GeneratedContent).count() == 1


def test_conversation_persists_student_and_tutor_messages_in_student_session():
    session, student, topic_id = _session()
    ai_session = start_ai_session(session, student.id, topic_id)

    response = respond_to_student(session, ai_session.id, _context(), "Why does it stop?")

    messages = session.query(AIMessage).filter_by(session_id=ai_session.id).all()
    assert response.role == "tutor"
    assert [message.role for message in messages] == ["student", "tutor"]


def test_teacher_overview_aggregates_mastery_without_exposing_messages():
    session, student, topic_id = _session()
    session.add(KnowledgeState(student_id=student.id, topic_id=topic_id, mastery_probability=0.31, mastery_level="Beginner"))
    session.flush()

    overview = class_overview(session)

    assert overview["student_count"] == 1
    assert overview["students_requiring_intervention"] == 1
    assert "messages" not in overview


def test_research_metrics_calculate_gains_and_prediction_quality():
    outcome = calculate_learning_outcome(40, 70)
    metrics = prediction_metrics([True, True, False], [True, False, False])

    assert outcome.learning_gain == 30
    assert outcome.normalized_gain == 0.5
    assert metrics["accuracy"] == 2 / 3
    assert metrics["f1"] == 2 / 3