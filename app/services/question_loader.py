"""Load validated question-dataset rows (CSV) into the questions/question_options
tables. Idempotent: if questions already exist for the subject, loading is skipped
so student responses already recorded against those question_ids are preserved."""
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Question, QuestionOption, Topic

OPTION_COLUMNS = ["option_a", "option_b", "option_c", "option_d"]


def load_questions_from_csv(session: Session, csv_path: str) -> int:
    if session.query(Question).count() > 0:
        return 0  # already loaded; skip to avoid breaking existing responses/FKs

    df = pd.read_csv(csv_path, keep_default_na=False)
    topics = session.query(Topic).all()
    name_to_id = {topic.name: topic.id for topic in topics}

    loaded = 0
    for _, row in df.iterrows():
        leaf_name = row["subtopic"] if str(row["subtopic"]).strip() else row["topic"]
        topic_id = name_to_id.get(leaf_name)
        if topic_id is None:
            continue  # topic not seeded; skip rather than fail the whole load

        question = Question(
            topic_id=topic_id,
            question_text=row["question_text"],
            question_type=row["question_type"],
            difficulty=row["difficulty"],
            correct_answer=row["correct_answer"],
            explanation=row.get("explanation", ""),
            marks=float(row["marks"]),
            source=row.get("source", "generated"),
        )
        session.add(question)
        session.flush()

        for col in OPTION_COLUMNS:
            option_text = str(row.get(col, "")).strip()
            if option_text == "":
                continue
            session.add(
                QuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=(option_text == str(row["correct_answer"]).strip()),
                )
            )
        loaded += 1

    session.commit()
    return loaded
