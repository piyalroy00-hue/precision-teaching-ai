"""Generate the base question dataset from the hand-authored question bank.

Writes data/generated/questions_generated.csv (and .json) with columns:
question_id, subject, topic, subtopic, question_type, difficulty, question_text,
option_a, option_b, option_c, option_d, correct_answer, explanation, marks, source.

Reproducible: iteration order is fixed (dict insertion order), no randomness used.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from app.config.settings import GENERATED_DATA_DIR, SUBJECT_NAME
from app.database.seed import TOPIC_TREE
from scripts.question_bank_data import QUESTION_BANK

OPTION_COLUMNS = ["option_a", "option_b", "option_c", "option_d"]


def _leaf_topic_subtopic_map() -> dict[str, tuple[str, str]]:
    """Map leaf topic name -> (topic column, subtopic column) using the topic tree."""
    mapping: dict[str, tuple[str, str]] = {}
    for node in TOPIC_TREE:
        children = node.get("children")
        if children:
            for child in children:
                mapping[child["name"]] = (node["name"], child["name"])
        else:
            mapping[node["name"]] = (node["name"], "")
    return mapping


def build_question_rows() -> list[dict]:
    topic_subtopic = _leaf_topic_subtopic_map()
    rows: list[dict] = []
    question_id = 1
    for leaf_topic, questions in QUESTION_BANK.items():
        topic, subtopic = topic_subtopic[leaf_topic]
        for q in questions:
            options = list(q["options"])
            options += [""] * (4 - len(options))  # pad to 4 columns (True/False has 2)
            correct_answer = q["options"][q["correct"]]
            row = {
                "question_id": question_id,
                "subject": SUBJECT_NAME,
                "topic": topic,
                "subtopic": subtopic,
                "question_type": q["type"],
                "difficulty": q["difficulty"],
                "question_text": q["text"],
                "option_a": options[0],
                "option_b": options[1],
                "option_c": options[2],
                "option_d": options[3],
                "correct_answer": correct_answer,
                "explanation": q["explanation"],
                "marks": q["marks"],
                "source": "generated",
            }
            rows.append(row)
            question_id += 1
    return rows


def main() -> None:
    rows = build_question_rows()
    df = pd.DataFrame(rows)

    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = GENERATED_DATA_DIR / "questions_generated.csv"
    json_path = GENERATED_DATA_DIR / "questions_generated.json"
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)

    print(f"Generated {len(df)} questions across {df['topic'].nunique()} top-level topics.")
    print(df["difficulty"].value_counts().to_string())
    print(f"Saved to:\n  {csv_path}\n  {json_path}")


if __name__ == "__main__":
    main()
