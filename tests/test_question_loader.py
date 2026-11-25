import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all models on Base
from app.database.db import Base
from app.database.seed import seed_subject_and_topics
from app.models import Question, QuestionOption
from app.services.question_loader import load_questions_from_csv

ROW = {
    "question_id": 1,
    "subject": "Python Programming",
    "topic": "Loops",
    "subtopic": "for Loop",
    "question_type": "MCQ",
    "difficulty": "Easy",
    "question_text": "What is printed by `for i in range(2): print(i)`?",
    "option_a": "0 1",
    "option_b": "1 2",
    "option_c": "",
    "option_d": "",
    "correct_answer": "0 1",
    "explanation": "range(2) yields 0 and 1.",
    "marks": 1,
    "source": "generated",
}


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
def csv_path(tmp_path):
    path = tmp_path / "questions.csv"
    pd.DataFrame([ROW]).to_csv(path, index=False)
    return str(path)


def test_load_questions_creates_question_and_options(session, csv_path):
    seed_subject_and_topics(session)
    loaded = load_questions_from_csv(session, csv_path)
    assert loaded == 1

    question = session.query(Question).one()
    assert question.question_text == ROW["question_text"]
    assert question.topic.name == "for Loop"

    options = session.query(QuestionOption).filter_by(question_id=question.id).all()
    assert len(options) == 2
    correct_options = [o for o in options if o.is_correct]
    assert len(correct_options) == 1
    assert correct_options[0].option_text == "0 1"


def test_load_questions_is_idempotent(session, csv_path):
    seed_subject_and_topics(session)
    load_questions_from_csv(session, csv_path)
    second_load = load_questions_from_csv(session, csv_path)
    assert second_load == 0
    assert session.query(Question).count() == 1
