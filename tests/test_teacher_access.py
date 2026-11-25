from app.main import create_app


def test_admin_can_open_teacher_dashboard():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    with client.session_transaction() as browser_session:
        browser_session.update(user_id=1, user_role="admin")

    response = client.get("/teacher/")

    assert response.status_code == 200


def test_student_cannot_open_teacher_dashboard():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    with client.session_transaction() as browser_session:
        browser_session.update(user_id=1, user_role="student")

    assert client.get("/teacher/").status_code == 403