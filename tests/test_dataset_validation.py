from pathlib import Path

import pandas as pd
import pytest

from app.config.settings import PROCESSED_DATA_DIR
from scripts.validate_questions import validate_dataframe, validate_question_row

VALID_ROW = {
    "question_id": 1,
    "subject": "Python Programming",
    "topic": "Loops",
    "subtopic": "for Loop",
    "question_type": "MCQ",
    "difficulty": "Easy",
    "question_text": "What is printed by `for i in range(2): print(i)`?",
    "option_a": "0 1",
    "option_b": "1 2",
    "option_c": "0 1 2",
    "option_d": "",
    "correct_answer": "0 1",
    "explanation": "range(2) yields 0 and 1.",
    "marks": 1,
}


def test_valid_row_has_no_errors():
    assert validate_question_row(VALID_ROW) == []


def test_missing_required_field_is_caught():
    row = dict(VALID_ROW, question_text="")
    errors = validate_question_row(row)
    assert any("question_text" in e for e in errors)


def test_invalid_difficulty_is_caught():
    row = dict(VALID_ROW, difficulty="Impossible")
    errors = validate_question_row(row)
    assert any("difficulty" in e for e in errors)


def test_invalid_question_type_is_caught():
    row = dict(VALID_ROW, question_type="ESSAY")
    errors = validate_question_row(row)
    assert any("question_type" in e for e in errors)


def test_non_positive_marks_is_caught():
    row = dict(VALID_ROW, marks=0)
    errors = validate_question_row(row)
    assert any("marks" in e for e in errors)


def test_correct_answer_not_in_options_is_caught():
    row = dict(VALID_ROW, correct_answer="Not an option")
    errors = validate_question_row(row)
    assert any("does not match any option" in e for e in errors)


def test_duplicate_options_are_caught():
    row = dict(VALID_ROW, option_b="0 1")  # duplicates option_a
    errors = validate_question_row(row)
    assert any("duplicate option" in e for e in errors)


def test_validate_dataframe_splits_valid_and_invalid():
    df = pd.DataFrame([VALID_ROW, dict(VALID_ROW, question_id=2, correct_answer="bad")])
    valid_df, error_df = validate_dataframe(df)
    assert len(valid_df) == 1
    assert len(error_df) == 1
    assert error_df.iloc[0]["question_id"] == 2


@pytest.mark.skipif(
    not (PROCESSED_DATA_DIR / "questions_final.csv").exists(),
    reason="processed dataset not generated yet",
)
def test_processed_dataset_is_fully_valid_and_unique():
    df = pd.read_csv(PROCESSED_DATA_DIR / "questions_final.csv", keep_default_na=False)
    valid_df, error_df = validate_dataframe(df)
    assert len(error_df) == 0
    assert df["question_id"].is_unique
