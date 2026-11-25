import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.ai.difficulty import recommended_difficulty
from app.ai.prerequisite_graph import prerequisites_for
from app.ai.recommender import score_resource
from app.database.db import Base
from app.database.resource_seed import seed_learning_resources
from app.database.seed import leaf_topic_ids, seed_subject_and_topics
from app.models import (
    Assessment,
    KnowledgeState,
    LearningResource,
    LearningSession,
    Question,
    Recommendation,
    Response,
    Subject,
    User,
)
from app.services.adaptive_assessment_service import choose_adaptive_question
from app.services.learning_service import (
    complete_learning_session,
    get_or_start_learning_session,
    start_learning_session,
)
from app.services.recommendation_service import build_learning_path


def test_prerequisite_graph_returns_function_skills_before_recursion():
    prerequisites = prerequisites_for("Recursion")
    assert "Function Definition" in prerequisites
    assert prerequisites.index("Function Definition") < prerequisites.index("Parameters and Arguments")


def test_difficulty_changes_only_one_level_after_full_window():
    assert recommended_difficulty([True] * 4, "Medium") == "Medium"
    assert recommended_difficulty([True] * 5, "Medium") == "Hard"
    assert recommended_difficulty([False] * 5, "Medium") == "Easy"


def test_low_mastery_scores_higher_priority_than_high_mastery():
    low = score_resource(0.28, 1.0, 1.0, 0.20, 1.0)
    high = score_resource(0.82, 0.25, 1.0, 0.80, 1.0)
    assert low.score > high.score
    assert low.priority == "High"


def test_learning_session_completion_marks_matching_recommendation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_subject_and_topics(session)
    seed_learning_resources(session)
    student = User(student_code="P2001", name="Phase Two", email="p2@example.test", password_hash="x")
    session.add(student)
    session.flush()
    resource = session.query(LearningResource).first()
    learning_session = start_learning_session(session, student.id, resource.id)
    completed = complete_learning_session(session, learning_session.id, student.id)
    assert completed.completion_percentage == 100.0
    assert completed.completed_at is not None


def test_personalized_paths_differ_for_distinct_mastery_profiles():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    topic_ids = seed_subject_and_topics(session)
    seed_learning_resources(session)
    student_a = User(student_code="P2002", name="A", email="a@example.test", password_hash="x")
    student_b = User(student_code="P2003", name="B", email="b@example.test", password_hash="x")
    session.add_all([student_a, student_b])
    session.flush()
    from app.services.knowledge_service import get_or_create_knowledge_state

    for topic_id in topic_ids.values():
        get_or_create_knowledge_state(session, student_a.id, topic_id).mastery_probability = 0.95
        get_or_create_knowledge_state(session, student_b.id, topic_id).mastery_probability = 0.95
    get_or_create_knowledge_state(session, student_a.id, topic_ids["Recursion"]).mastery_probability = 0.28
    get_or_create_knowledge_state(session, student_b.id, topic_ids["Recursion"]).mastery_probability = 0.82
    path_a = build_learning_path(session, student_a.id)
    path_b = build_learning_path(session, student_b.id)
    assert path_a[0]["difficulty"] == "Easy"
    assert path_b[0]["difficulty"] in {"Medium", "Hard"}


def test_question_selection_avoids_previous_question_when_an_unseen_one_exists():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    topic_id = seed_subject_and_topics(session)["Recursion"]
    student = User(student_code="P2004", name="Selector", email="selector@example.test", password_hash="x")
    subject = session.query(Subject).one()
    session.add(student)
    session.flush()
    assessment = Assessment(student_id=student.id, subject_id=subject.id)
    session.add(assessment)
    session.flush()
    seen = Question(
        topic_id=topic_id, question_text="Seen", question_type="MCQ", difficulty="Easy",
        correct_answer="a", explanation="Seen question", marks=1.0, source="generated",
    )
    unseen = Question(
        topic_id=topic_id, question_text="Unseen", question_type="MCQ", difficulty="Easy",
        correct_answer="b", explanation="Unseen question", marks=1.0, source="generated",
    )
    session.add_all([seen, unseen])
    session.flush()
    session.add(Response(
        assessment_id=assessment.id, student_id=student.id, question_id=seen.id, answer="a", is_correct=True,
        score=1.0, time_taken=0.0, attempt_number=1,
    ))
    session.flush()

    chosen = choose_adaptive_question(session, student_id=student.id, topic_id=topic_id, difficulty="Easy")

    assert chosen.id == unseen.id


def test_question_selection_handles_empty_bank():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    topic_id = seed_subject_and_topics(session)["Recursion"]

    assert choose_adaptive_question(session, student_id=1, topic_id=topic_id, difficulty="Easy") is None


def test_complete_learning_session_rejects_another_student():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_subject_and_topics(session)
    seed_learning_resources(session)
    owner = User(student_code="P2005", name="Owner", email="owner@example.test", password_hash="x")
    attacker = User(student_code="P2006", name="Attacker", email="attacker@example.test", password_hash="x")
    session.add_all([owner, attacker])
    session.flush()
    resource_id = session.query(LearningResource.id).first()[0]
    learning_session = start_learning_session(session, owner.id, resource_id)

    with pytest.raises(ValueError, match="does not belong"):
        complete_learning_session(session, learning_session.id, attacker.id)


def test_learning_session_lookup_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_subject_and_topics(session)
    seed_learning_resources(session)
    student = User(student_code="P2007", name="Revisitor", email="revisitor@example.test", password_hash="x")
    session.add(student)
    session.flush()
    resource_id = session.query(LearningResource.id).first()[0]

    first = get_or_start_learning_session(session, student.id, resource_id)
    second = get_or_start_learning_session(session, student.id, resource_id)

    assert first.id == second.id
    assert session.query(LearningSession).count() == 1


def test_learning_path_only_tracks_leaf_topics():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_subject_and_topics(session)
    seed_learning_resources(session)
    student = User(student_code="P2008", name="Leaves", email="leaves@example.test", password_hash="x")
    session.add(student)
    session.flush()

    path = build_learning_path(session, student.id)

    expected_leaf_ids = set(leaf_topic_ids(session))
    assert path
    assert {item["topic_id"] for item in path} <= expected_leaf_ids
    assert {
        state.topic_id for state in session.query(KnowledgeState).filter_by(student_id=student.id)
    } == expected_leaf_ids


def test_learning_path_preserves_in_progress_recommendations():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_subject_and_topics(session)
    seed_learning_resources(session)
    student = User(student_code="P2009", name="Pending", email="pending@example.test", password_hash="x")
    session.add(student)
    session.flush()

    build_learning_path(session, student.id, limit=1)
    pending = session.query(Recommendation).one()
    start_learning_session(session, student.id, pending.resource_id)
    build_learning_path(session, student.id, limit=1)

    refreshed = session.get(Recommendation, pending.id)
    assert refreshed is not None
    assert refreshed.completed is False
