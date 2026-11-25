import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database.db import Base
from app.database.seed import seed_subject_and_topics
from app.models import Assessment, KnowledgeState, Subject, User
from app.services.admin_service import delete_user
from app.services.admin_service import reset_user_password
from app.utils.security import verify_password


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    yield db_session
    db_session.close()


def test_delete_user_removes_dependent_learning_records(session):
    topic_id = seed_subject_and_topics(session)["Recursion"]
    subject = session.query(Subject).one()
    admin = User(student_code="ADMIN001", name="Admin", email="admin@test.local", password_hash="x", role="admin")
    student = User(student_code="USER001", name="Student", email="student@test.local", password_hash="x")
    session.add_all([admin, student])
    session.flush()
    session.add(KnowledgeState(student_id=student.id, topic_id=topic_id, mastery_probability=0.2, mastery_level="Beginner"))
    session.add(Assessment(student_id=student.id, subject_id=subject.id))
    session.flush()

    delete_user(session, student.id, admin.id)

    assert session.get(User, student.id) is None
    assert session.query(KnowledgeState).filter_by(student_id=student.id).count() == 0
    assert session.query(Assessment).filter_by(student_id=student.id).count() == 0


def test_delete_user_rejects_self_deletion(session):
    admin = User(student_code="ADMIN002", name="Admin", email="admin2@test.local", password_hash="x", role="admin")
    session.add(admin)
    session.flush()

    with pytest.raises(ValueError, match="own account"):
        delete_user(session, admin.id, admin.id)


def test_reset_user_password_replaces_only_the_stored_hash(session):
    user = User(student_code="USER002", name="Student", email="student2@test.local", password_hash="old")
    session.add(user)
    session.flush()

    reset_user_password(session, user.id, "new-password")

    assert user.password_hash != "new-password"
    assert verify_password("new-password", user.password_hash)