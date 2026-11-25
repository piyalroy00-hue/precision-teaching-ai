"""Generate a reproducible, clearly labelled synthetic Phase 2 resource dataset."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.prerequisite_graph import prerequisites_for
from app.config.settings import GENERATED_DATA_DIR
from app.database.seed import LEAF_TOPIC_NAMES

RESOURCE_TYPES = ("explanation", "example", "worked_example", "practice", "summary", "exercise")
FIELDNAMES = (
    "resource_id", "topic", "subtopic", "title", "content", "resource_type", "difficulty",
    "estimated_minutes", "prerequisite", "learning_objective", "data_source",
)


def generate_learning_resources() -> list[dict[str, str | int]]:
    """Return deterministic synthetic resources; no human-authorship is implied."""
    rows: list[dict[str, str | int]] = []
    resource_id = 1
    for topic in LEAF_TOPIC_NAMES:
        prerequisite = "; ".join(prerequisites_for(topic, recursive=False))
        for index, resource_type in enumerate(RESOURCE_TYPES):
            difficulty = ("Easy", "Medium", "Hard")[index % 3]
            rows.append({
                "resource_id": resource_id,
                "topic": topic,
                "subtopic": topic,
                "title": f"{topic}: {resource_type.replace('_', ' ').title()}",
                "content": f"Synthetic learning material for {topic} at {difficulty} difficulty.",
                "resource_type": resource_type,
                "difficulty": difficulty,
                "estimated_minutes": 10 + index * 5,
                "prerequisite": prerequisite,
                "learning_objective": f"Apply {topic} accurately in a Python program.",
                "data_source": "synthetic",
            })
            resource_id += 1
    return rows


def main() -> None:
    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = GENERATED_DATA_DIR / "learning_resources_synthetic.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(generate_learning_resources())
    print(f"Wrote {len(generate_learning_resources())} synthetic resources to {output}")


if __name__ == "__main__":
    main()