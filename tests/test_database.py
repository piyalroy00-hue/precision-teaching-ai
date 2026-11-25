import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base
import app.models  # noqa: F401 - registers all models on Base
from app.database.seed import LEAF_TOPIC_NAMES, seed_subject_and_topics
from app.models import Subject, Topic, User


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


def test_seed_creates_subject_and_all_topics(session):
    topic_ids = seed_subject_and_topics(session)
    assert session.query(Subject).count() == 1
    # 11 top-level topics + 6 nested children (2 under Loops, 4 under Functions) = 17
    assert session.query(Topic).count() == 17
    for leaf_name in LEAF_TOPIC_NAMES:
        assert leaf_name in topic_ids


def test_seed_is_idempotent(session):
    seed_subject_and_topics(session)
    seed_subject_and_topics(session)
    assert session.query(Subject).count() == 1
    assert session.query(Topic).count() == 17


def test_topic_parent_child_relationship(session):
    seed_subject_and_topics(session)
    loops = session.query(Topic).filter_by(name="Loops").one()
    child_names = {child.name for child in loops.children}
    assert child_names == {"for Loop", "while Loop"}


def test_user_can_be_created_and_queried(session):
    user = User(
        student_code="STU0001",
        name="Test Student",
        email="test.student@example.test",
        password_hash="hashed",
        role="student",
    )
    session.add(user)
    session.commit()

    fetched = session.query(User).filter_by(student_code="STU0001").one()
    assert fetched.name == "Test Student"
    assert fetched.role == "student"
