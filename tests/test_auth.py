import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all models on Base
from app.database.db import Base
from app.services.auth_service import AuthError, authenticate, register_student


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


def test_register_and_authenticate_round_trip(session):
    user = register_student(
        session,
        student_code="CS2026001",
        name="Asha Verma",
        email="asha@example.test",
        password="StrongPass1!",
    )
    assert user.id is not None
    assert user.password_hash != "StrongPass1!"  # never store plaintext

    authenticated = authenticate(session, "asha@example.test", "StrongPass1!")
    assert authenticated.id == user.id


def test_authenticate_rejects_wrong_password(session):
    register_student(
        session, student_code="CS2026002", name="Bob", email="bob@example.test", password="Correct1!"
    )
    with pytest.raises(AuthError):
        authenticate(session, "bob@example.test", "WrongPassword")


def test_authenticate_rejects_unknown_email(session):
    with pytest.raises(AuthError):
        authenticate(session, "nobody@example.test", "whatever")


def test_register_rejects_duplicate_email(session):
    register_student(
        session, student_code="CS2026003", name="Carl", email="carl@example.test", password="Pass1234!"
    )
    with pytest.raises(AuthError):
        register_student(
            session, student_code="CS2026004", name="Carl2", email="carl@example.test", password="Pass1234!"
        )


def test_register_rejects_duplicate_student_code(session):
    register_student(
        session, student_code="CS2026005", name="Dana", email="dana@example.test", password="Pass1234!"
    )
    with pytest.raises(AuthError):
        register_student(
            session, student_code="CS2026005", name="Dana2", email="dana2@example.test", password="Pass1234!"
        )
