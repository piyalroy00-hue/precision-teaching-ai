"""Create a deterministic, anonymized synthetic evaluation dataset for development only."""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import GENERATED_DATA_DIR, RANDOM_SEED
from app.database.seed import LEAF_TOPIC_NAMES
from ml.evaluation.metrics import calculate_learning_outcome


def main() -> None:
    randomizer = random.Random(RANDOM_SEED)
    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for number in range(1, 31):
        group = "experimental" if number % 2 == 0 else "control"
        for topic in LEAF_TOPIC_NAMES:
            pretest = round(randomizer.uniform(25, 70), 1)
            intervention_gain = randomizer.uniform(8, 24) if group == "experimental" else randomizer.uniform(3, 16)
            posttest = round(min(100, pretest + intervention_gain), 1)
            outcome = calculate_learning_outcome(pretest, posttest)
            initial_mastery = round(pretest / 100, 3)
            final_mastery = round(min(1, posttest / 100), 3)
            rows.append({
                "student_id": f"ANON-{number:03d}", "group": group, "topic": topic,
                "pretest_score": pretest, "posttest_score": posttest,
                "learning_gain": round(outcome.learning_gain, 3),
                "normalized_gain": round(outcome.normalized_gain or 0.0, 3),
                "time_to_mastery": randomizer.randint(15, 90),
                "attempt_count": randomizer.randint(3, 12),
                "initial_mastery": initial_mastery, "final_mastery": final_mastery,
                "recommendations_completed": randomizer.randint(0, 5) if group == "experimental" else 0,
                "ai_sessions": randomizer.randint(0, 4) if group == "experimental" else 0,
                "data_source": "synthetic",
            })
    output = GENERATED_DATA_DIR / "research_evaluation_synthetic.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} anonymized synthetic research rows to {output}")


if __name__ == "__main__":
    main()