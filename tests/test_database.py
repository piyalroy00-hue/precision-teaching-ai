import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base
import app.models  # noqa: F401 - registers all models on Base
from app.database.seed import LEAF_TOPIC_NAMES, leaf_topic_ids, seed_subject_and_topics
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


def test_leaf_topic_ids_exclude_parent_topics(session):
    topic_ids = seed_subject_and_topics(session)

    leaf_ids = set(leaf_topic_ids(session))

    assert leaf_ids == {topic_ids[name] for name in LEAF_TOPIC_NAMES}
    assert topic_ids["Loops"] not in leaf_ids
    assert topic_ids["Functions"] not in leaf_ids


def test_sqlite_foreign_keys_are_enabled():
    from app.database.db import engine

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
