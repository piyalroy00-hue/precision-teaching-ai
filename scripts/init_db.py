"""Create the SQLite schema and seed the fixed subject/topic hierarchy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.db import get_session, init_db
from app.database.seed import seed_subject_and_topics


def main() -> None:
    init_db()
    with get_session() as session:
        topic_ids = seed_subject_and_topics(session)
    print(f"Database initialized. {len(topic_ids)} topics present:")
    for name, tid in topic_ids.items():
        print(f"  [{tid}] {name}")


if __name__ == "__main__":
    main()
