from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database.db import Base
from app.database.seed import seed_subject_and_topics
from app.models import KnowledgeState, User
from app.services.teacher_analytics_service import all_student_performance


def test_all_student_performance_returns_mastery_and_intervention_status():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    topic_id = seed_subject_and_topics(session)["Recursion"]
    student = User(student_code="PERF001", name="Performance Student", email="performance@test.local", password_hash="x")
    session.add(student)
    session.flush()
    session.add(KnowledgeState(student_id=student.id, topic_id=topic_id, mastery_probability=0.30, mastery_level="Beginner"))
    session.flush()

    performance = all_student_performance(session)

    assert performance[0]["average_mastery"] == 0.30
    assert performance[0]["requires_intervention"] is True