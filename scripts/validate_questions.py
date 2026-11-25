"""Validate question records for structural and answer-key correctness.

Usable as a CLI (validates an input CSV, writes processed output) or as an
importable module (validate_question_row / validate_dataframe) for reuse in
augment_questions.py and the test suite.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from app.config.settings import AUGMENTED_DATA_DIR, PROCESSED_DATA_DIR

VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
VALID_QUESTION_TYPES = {"MCQ", "TRUE_FALSE", "SHORT_ANSWER"}
OPTION_COLUMNS = ["option_a", "option_b", "option_c", "option_d"]


def validate_question_row(row: dict) -> list[str]:
    """Return a list of validation error messages for a single question row (empty = valid)."""
    errors: list[str] = []

    for field in ("subject", "topic", "question_text", "correct_answer"):
        value = row.get(field)
        if value is None or str(value).strip() == "":
            errors.append(f"missing required field '{field}'")

    difficulty = row.get("difficulty")
    if difficulty not in VALID_DIFFICULTIES:
        errors.append(f"invalid difficulty '{difficulty}'")

    question_type = row.get("question_type")
    if question_type not in VALID_QUESTION_TYPES:
        errors.append(f"invalid question_type '{question_type}'")

    try:
        marks = float(row.get("marks", 0))
        if marks <= 0:
            errors.append(f"marks must be > 0, got {marks}")
    except (TypeError, ValueError):
        errors.append(f"marks is not numeric: {row.get('marks')!r}")

    if question_type in ("MCQ", "TRUE_FALSE"):
        options = [
            str(row.get(col)).strip()
            for col in OPTION_COLUMNS
            if row.get(col) is not None and str(row.get(col)).strip() != ""
        ]
        if len(options) < 2:
            errors.append(f"expected at least 2 non-empty options, found {len(options)}")
        if len(options) != len(set(options)):
            errors.append("duplicate option text found")
        correct_answer = str(row.get("correct_answer", "")).strip()
        if correct_answer not in options:
            errors.append(
                f"correct_answer {correct_answer!r} does not match any option {options!r}"
            )

    return errors


def validate_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a dataframe into (valid_rows, error_report) based on per-row validation."""
    error_records = []
    valid_mask = []
    for _, row in df.iterrows():
        errors = validate_question_row(row.to_dict())
        valid_mask.append(len(errors) == 0)
        if errors:
            error_records.append(
                {"question_id": row.get("question_id"), "errors": "; ".join(errors)}
            )
    valid_df = df[pd.Series(valid_mask, index=df.index)].reset_index(drop=True)
    error_df = pd.DataFrame(error_records)
    return valid_df, error_df


def main() -> None:
    input_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else AUGMENTED_DATA_DIR / "questions_augmented.csv"
    )
    df = pd.read_csv(input_path, keep_default_na=False)
    valid_df, error_df = validate_dataframe(df)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    valid_path = PROCESSED_DATA_DIR / "questions_final.csv"
    errors_path = PROCESSED_DATA_DIR / "validation_errors.csv"
    valid_df.to_csv(valid_path, index=False)
    error_df.to_csv(errors_path, index=False)

    print(f"Validated {len(df)} questions from {input_path}")
    print(f"  Valid:   {len(valid_df)} -> {valid_path}")
    print(f"  Invalid: {len(error_df)} -> {errors_path}")
    if len(error_df) > 0:
        print(error_df.to_string(index=False))


if __name__ == "__main__":
    main()
