"""Seed the fixed Python Programming subject/topic hierarchy (idempotent)."""
from sqlalchemy.orm import Session

from app.config.settings import SUBJECT_NAME
from app.models import Subject, Topic

# Leaf nodes (no "children") are where questions attach directly.
TOPIC_TREE = [
    {"name": "Variables and Data Types", "difficulty_level": "Easy"},
    {"name": "Operators", "difficulty_level": "Easy"},
    {"name": "Conditional Statements", "difficulty_level": "Easy"},
    {
        "name": "Loops",
        "difficulty_level": "Medium",
        "children": [
            {"name": "for Loop", "difficulty_level": "Medium"},
            {"name": "while Loop", "difficulty_level": "Medium"},
        ],
    },
    {
        "name": "Functions",
        "difficulty_level": "Medium",
        "children": [
            {"name": "Function Definition", "difficulty_level": "Medium"},
            {"name": "Parameters and Arguments", "difficulty_level": "Medium"},
            {"name": "Return Values", "difficulty_level": "Medium"},
            {"name": "Variable Scope", "difficulty_level": "Hard"},
        ],
    },
    {"name": "Lists", "difficulty_level": "Medium"},
    {"name": "Tuples", "difficulty_level": "Easy"},
    {"name": "Dictionaries", "difficulty_level": "Medium"},
    {"name": "Exception Handling", "difficulty_level": "Hard"},
    {"name": "File Handling", "difficulty_level": "Hard"},
    {"name": "Recursion", "difficulty_level": "Hard"},
]


def seed_subject_and_topics(session: Session) -> dict[str, int]:
    """Create the subject + topic hierarchy if missing. Returns {topic_name: topic_id}."""
    subject = session.query(Subject).filter_by(name=SUBJECT_NAME).one_or_none()
    if subject is None:
        subject = Subject(
            name=SUBJECT_NAME,
            description="Core Python programming concepts for diagnostic assessment.",
            semester=1,
        )
        session.add(subject)
        session.flush()

    topic_ids: dict[str, int] = {}

    def _create(node: dict, parent_id: int | None) -> None:
        topic = (
            session.query(Topic)
            .filter_by(subject_id=subject.id, name=node["name"], parent_topic_id=parent_id)
            .one_or_none()
        )
        if topic is None:
            topic = Topic(
                subject_id=subject.id,
                parent_topic_id=parent_id,
                name=node["name"],
                difficulty_level=node.get("difficulty_level"),
            )
            session.add(topic)
            session.flush()
        topic_ids[node["name"]] = topic.id
        for child in node.get("children", []):
            _create(child, parent_id=topic.id)

    for node in TOPIC_TREE:
        _create(node, parent_id=None)

    session.commit()
    return topic_ids


LEAF_TOPIC_NAMES = [
    "Variables and Data Types",
    "Operators",
    "Conditional Statements",
    "for Loop",
    "while Loop",
    "Function Definition",
    "Parameters and Arguments",
    "Return Values",
    "Variable Scope",
    "Lists",
    "Tuples",
    "Dictionaries",
    "Exception Handling",
    "File Handling",
    "Recursion",
]


def leaf_topic_ids(session: Session) -> list[int]:
    """Return IDs for topics that have no child topics."""
    parent_ids = {
        parent_id
        for (parent_id,) in (
            session.query(Topic.parent_topic_id)
            .filter(Topic.parent_topic_id.isnot(None))
            .all()
        )
    }
    return [
        topic.id
        for topic in session.query(Topic).order_by(Topic.id)
        if topic.id not in parent_ids
    ]
