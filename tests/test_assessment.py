import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all models on Base
from app.database.db import Base
from app.database.seed import seed_subject_and_topics
from app.models import KnowledgeState, Question, QuestionOption, Subject, User
from app.services.assessment_service import (
    complete_assessment,
    get_fixed_diagnostic_questions,
    start_assessment,
    submit_response,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def seeded(session):
    topic_ids = seed_subject_and_topics(session)
    subject = session.query(Subject).one()

    q1 = Question(
        topic_id=topic_ids["Variables and Data Types"],
        question_text="What is 2 + 2?",
        question_type="MCQ",
        difficulty="Easy",
        correct_answer="4",
        explanation="Basic addition.",
        marks=1.0,
        source="generated",
    )
    q2 = Question(
        topic_id=topic_ids["Recursion"],
        question_text="Does every recursive function need a base case?",
        question_type="TRUE_FALSE",
        difficulty="Easy",
        correct_answer="True",
        explanation="Prevents infinite recursion.",
        marks=1.0,
        source="generated",
    )
    session.add_all([q1, q2])
    session.flush()
    session.add_all(
        [
            QuestionOption(question_id=q1.id, option_text="3", is_correct=False),
            QuestionOption(question_id=q1.id, option_text="4", is_correct=True),
            QuestionOption(question_id=q2.id, option_text="True", is_correct=True),
            QuestionOption(question_id=q2.id, option_text="False", is_correct=False),
        ]
    )

    student = User(
        student_code="STU0001",
        name="Test Student",
        email="test@example.test",
        password_hash="hash",
        role="student",
    )
    session.add(student)
    session.commit()

    return {"subject": subject, "student": student, "q1": q1, "q2": q2}


def test_fixed_diagnostic_returns_only_generated_questions(session, seeded):
    questions = get_fixed_diagnostic_questions(session, seeded["subject"].id)
    assert len(questions) == 2
    assert all(q.source == "generated" for q in questions)


def test_submit_correct_response_scores_full_marks_and_updates_mastery(session, seeded):
    assessment = start_assessment(session, seeded["student"].id, seeded["subject"].id)
    response = submit_response(
        session, assessment.id, seeded["student"].id, seeded["q1"].id, answer="4", time_taken=10.0
    )
    assert response.is_correct is True
    assert response.score == 1.0
    assert response.attempt_number == 1

    state = (
        session.query(KnowledgeState)
        .filter_by(student_id=seeded["student"].id, topic_id=seeded["q1"].topic_id)
        .one()
    )
    assert state.mastery_probability > 0.20  # increased from BKT default p_init


def test_submit_incorrect_response_scores_zero_and_lowers_mastery(session, seeded):
    assessment = start_assessment(session, seeded["student"].id, seeded["subject"].id)
    response = submit_response(
        session, assessment.id, seeded["student"].id, seeded["q1"].id, answer="3", time_taken=8.0
    )
    assert response.is_correct is False
    assert response.score == 0.0

    state = (
        session.query(KnowledgeState)
        .filter_by(student_id=seeded["student"].id, topic_id=seeded["q1"].topic_id)
        .one()
    )
    assert state.mastery_probability < 0.20


def test_repeated_attempts_increment_attempt_number(session, seeded):
    assessment = start_assessment(session, seeded["student"].id, seeded["subject"].id)
    r1 = submit_response(session, assessment.id, seeded["student"].id, seeded["q1"].id, answer="4")
    r2 = submit_response(session, assessment.id, seeded["student"].id, seeded["q1"].id, answer="3")
    assert r1.attempt_number == 1
    assert r2.attempt_number == 2


def test_complete_assessment_computes_score_and_percentage(session, seeded):
    assessment = start_assessment(session, seeded["student"].id, seeded["subject"].id)
    submit_response(session, assessment.id, seeded["student"].id, seeded["q1"].id, answer="4")
    submit_response(session, assessment.id, seeded["student"].id, seeded["q2"].id, answer="False")

    completed = complete_assessment(session, assessment.id)
    assert completed.completed_at is not None
    assert completed.total_score == 1.0
    assert completed.percentage == pytest.approx(50.0)
