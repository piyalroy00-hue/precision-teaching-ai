"""Flask application entry point for the Precision Teaching AI project."""
from __future__ import annotations

from flask import Flask

from app.blueprints.auth import bp as auth_bp
from app.blueprints.admin import bp as admin_bp
from app.blueprints.student import bp as student_bp
from app.blueprints.teacher import bp as teacher_bp
from app.config.settings import PROCESSED_DATA_DIR
from app.database.db import get_session, init_db
from app.database.resource_seed import seed_learning_resources
from app.database.seed import seed_subject_and_topics
from app.services.question_loader import load_questions_from_csv

_bootstrapped = False


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "precision-teaching-dev-key"

    @app.before_request
    def before_request() -> None:
        bootstrap()

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    return app


def bootstrap() -> None:
    """Create tables and seed data once during app startup."""
    global _bootstrapped
    if _bootstrapped:
        return
    init_db()
    with get_session() as db_session:
        seed_subject_and_topics(db_session)
        seed_learning_resources(db_session)
        csv_path = PROCESSED_DATA_DIR / "questions_final.csv"
        if csv_path.exists():
            load_questions_from_csv(db_session, str(csv_path))
    _bootstrapped = True


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
