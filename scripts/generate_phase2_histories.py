"""Generate reproducible synthetic Phase 2 interaction histories for analysis/testing."""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import GENERATED_DATA_DIR, RANDOM_SEED
from app.database.seed import LEAF_TOPIC_NAMES

STUDENT_LIMIT = 10


def _load_student_codes() -> list[str]:
    path = GENERATED_DATA_DIR / "synthetic_students.csv"
    if not path.exists():
        raise SystemExit("Run scripts/generate_students.py before generating Phase 2 histories.")
    with path.open(newline="", encoding="utf-8") as handle:
        return [row["student_code"] for row in csv.DictReader(handle)][:STUDENT_LIMIT]


def main() -> None:
    randomizer = random.Random(RANDOM_SEED)
    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    student_codes = _load_student_codes()
    sessions, responses = [], []
    for index, student_code in enumerate(student_codes, start=1):
        student_number = int(student_code.removeprefix("SYN"))
        for topic in LEAF_TOPIC_NAMES:
            sessions.append({"student_code": student_code, "topic": topic, "completion_percentage": 100, "data_source": "synthetic"})
            difficulty = 1
            for attempt in range(1, 7):
                probability = min(0.85, 0.30 + attempt * 0.08 + index * 0.01)
                correct = randomizer.random() < probability
                if correct and difficulty < 3:
                    difficulty += 1
                elif not correct and difficulty > 1:
                    difficulty -= 1
                responses.append({"student_code": student_code, "topic": topic, "attempt": attempt, "is_correct": correct, "difficulty": ("Easy", "Medium", "Hard")[difficulty - 1], "data_source": "synthetic"})
    for name, rows in (("synthetic_learning_sessions.csv", sessions), ("synthetic_adaptive_responses.csv", responses)):
        with (GENERATED_DATA_DIR / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(f"Wrote {len(sessions)} synthetic sessions and {len(responses)} synthetic adaptive responses.")


if __name__ == "__main__":
    main()