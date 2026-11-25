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


def test_registration_and_authentication_normalize_email(session):
    user = register_student(
        session, student_code="CS2026006", name="Case Test", email="Case@Example.Test", password="Pass1234!"
    )

    assert user.email == "case@example.test"
    assert authenticate(session, "CASE@EXAMPLE.TEST", "Pass1234!").id == user.id


def test_setup_admin_route_is_not_exposed(monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(main_module, "bootstrap", lambda: None)
    app = main_module.create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    assert client.get("/setup-admin").status_code == 404
    assert client.post("/setup-admin", data={"email": "x@example.test"}).status_code == 404


def test_logged_in_role_selects_landing_page(monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(main_module, "bootstrap", lambda: None)
    app = main_module.create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    for role, expected_location in (
        ("admin", "/admin/"),
        ("teacher", "/teacher/"),
        ("student", "/dashboard"),
    ):
        with client.session_transaction() as browser_session:
            browser_session.clear()
            browser_session.update(user_id=1, user_role=role)
        response = client.get("/")
        assert response.headers["Location"] == expected_location
