"""Generate SYNTHETIC student-response interaction data for BKT development.

*** SYNTHETIC DATA - not real student records. Every row is programmatically
*** simulated from a learner-profile model with realistic noise; see
*** generate_students.py for the profile definitions.

Each student answers a handful of questions per topic across several
simulated assessment sessions (spaced in time), so that mastery-over-time
trends (needed by BKT) are present in the data. Correctness is drawn
probabilistically per response - not hard-coded - so a "strong" learner can
still occasionally miss a question and a "weak" learner can still get one
right.
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from app.config.settings import GENERATED_DATA_DIR, PROCESSED_DATA_DIR, RANDOM_SEED

N_SESSIONS = 4
QUESTIONS_PER_TOPIC_PER_SESSION = 2
BASE_DATE = datetime(2026, 1, 5)
DIFFICULTY_PENALTY = {"Easy": 0.10, "Medium": 0.0, "Hard": -0.18}
DIFFICULTY_TIME_SECONDS = {"Easy": 20.0, "Medium": 35.0, "Hard": 55.0}


def _leaf_topic(row: pd.Series) -> str:
    return row["subtopic"] if str(row.get("subtopic", "")).strip() else row["topic"]


def _correctness_probability(student: pd.Series, topic: str, difficulty: str, session_index: int, rng: random.Random) -> float:
    ability = float(student["base_ability"])

    if student["learning_profile"] == "improving":
        ability = min(ability + session_index * 0.12, 0.95)
    elif student["learning_profile"] == "topic_specific":
        if topic == student["specialty_topic"]:
            ability = min(ability + 0.35, 0.95)
        else:
            ability = max(ability - 0.15, 0.05)

    prob = ability + DIFFICULTY_PENALTY[difficulty]
    prob += rng.gauss(0, float(student["variance"]))
    return min(max(prob, 0.02), 0.98)


def _sample_time_taken(difficulty: str, is_correct: bool, rng: random.Random) -> float:
    mean = DIFFICULTY_TIME_SECONDS[difficulty] * (0.9 if is_correct else 1.15)
    value = rng.gauss(mean, mean * 0.3)
    return round(max(value, 3.0), 1)


def generate_responses(questions_df: pd.DataFrame, students_df: pd.DataFrame) -> pd.DataFrame:
    questions_df = questions_df.copy()
    questions_df["leaf_topic"] = questions_df.apply(_leaf_topic, axis=1)
    questions_by_topic = {
        topic: group.to_dict("records") for topic, group in questions_df.groupby("leaf_topic")
    }

    rows = []
    response_id = 1
    for _, student in students_df.iterrows():
        attempt_counters: dict[str, int] = {}
        for session_index in range(N_SESSIONS):
            session_rng = random.Random(RANDOM_SEED + int(student["student_id"]) * 1000 + session_index)
            session_date = BASE_DATE + timedelta(days=session_index * 7, hours=session_rng.randint(0, 6))

            for topic, pool in questions_by_topic.items():
                k = min(QUESTIONS_PER_TOPIC_PER_SESSION, len(pool))
                sampled = session_rng.sample(pool, k=k)
                for question in sampled:
                    prob = _correctness_probability(student, topic, question["difficulty"], session_index, session_rng)
                    is_correct = session_rng.random() < prob
                    time_taken = _sample_time_taken(question["difficulty"], is_correct, session_rng)
                    attempt_counters[topic] = attempt_counters.get(topic, 0) + 1
                    timestamp = session_date + timedelta(minutes=session_rng.randint(0, 240))

                    rows.append(
                        {
                            "response_id": response_id,
                            "student_id": student["student_id"],
                            "question_id": question["question_id"],
                            "topic": topic,
                            "difficulty": question["difficulty"],
                            "correct": is_correct,
                            "time_taken": time_taken,
                            "attempt_number": attempt_counters[topic],
                            "timestamp": timestamp.isoformat(),
                            "data_source": "synthetic",
                        }
                    )
                    response_id += 1

    return pd.DataFrame(rows)


def main() -> None:
    questions_df = pd.read_csv(PROCESSED_DATA_DIR / "questions_final.csv", keep_default_na=False)
    students_df = pd.read_csv(GENERATED_DATA_DIR / "synthetic_students.csv", keep_default_na=False)

    responses_df = generate_responses(questions_df, students_df)

    out_path = GENERATED_DATA_DIR / "synthetic_responses.csv"
    responses_df.to_csv(out_path, index=False)

    accuracy_by_profile = (
        responses_df.merge(students_df, on="student_id")
        .groupby("learning_profile")["correct"]
        .mean()
        .round(3)
    )
    print(f"Generated {len(responses_df)} SYNTHETIC responses for {students_df.shape[0]} students.")
    print("Accuracy by learning profile:")
    print(accuracy_by_profile.to_string())
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
