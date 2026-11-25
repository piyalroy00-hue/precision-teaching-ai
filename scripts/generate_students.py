"""Generate SYNTHETIC student profiles for BKT development and testing.

*** This data is entirely synthetic / fabricated and must never be presented
*** as real student data. It exists only to exercise the BKT pipeline before
*** real diagnostic-assessment data is available.

Learning profiles (base_ability in [0, 1], higher = more likely to answer
correctly; modifiers are applied per-response in generate_responses.py):
  - strong        : high base ability, low variance
  - average       : medium base ability, medium variance
  - slow          : below-average ability, learns steadily but slowly
  - weak          : low base ability, struggles across most topics
  - topic_specific: average ability overall, but strongly boosted on one topic
  - improving     : starts low, ability increases noticeably across sessions
  - inconsistent  : medium ability but high response-to-response variance
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from faker import Faker

from app.config.settings import GENERATED_DATA_DIR, RANDOM_SEED
from app.database.seed import LEAF_TOPIC_NAMES

PROFILES = {
    "strong": {"base_ability": 0.88, "variance": 0.05},
    "average": {"base_ability": 0.62, "variance": 0.12},
    "slow": {"base_ability": 0.45, "variance": 0.10},
    "weak": {"base_ability": 0.28, "variance": 0.10},
    "topic_specific": {"base_ability": 0.55, "variance": 0.12},
    "improving": {"base_ability": 0.35, "variance": 0.10},
    "inconsistent": {"base_ability": 0.55, "variance": 0.30},
}

STUDENTS_PER_PROFILE = 4


def generate_students() -> pd.DataFrame:
    fake = Faker()
    Faker.seed(RANDOM_SEED)
    rng_state = RANDOM_SEED

    rows = []
    student_id = 1
    for profile_name, params in PROFILES.items():
        for i in range(STUDENTS_PER_PROFILE):
            specialty_topic = (
                LEAF_TOPIC_NAMES[(student_id * 3) % len(LEAF_TOPIC_NAMES)]
                if profile_name == "topic_specific"
                else ""
            )
            rows.append(
                {
                    "student_id": student_id,
                    "student_code": f"SYN{student_id:04d}",
                    "name": fake.name(),
                    "email": f"syn.student{student_id:04d}@example-synthetic.test",
                    "learning_profile": profile_name,
                    "base_ability": params["base_ability"],
                    "variance": params["variance"],
                    "specialty_topic": specialty_topic,
                    "data_source": "synthetic",
                }
            )
            student_id += 1
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_students()
    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GENERATED_DATA_DIR / "synthetic_students.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} SYNTHETIC student profiles across {df['learning_profile'].nunique()} learner types.")
    print(df["learning_profile"].value_counts().to_string())
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
