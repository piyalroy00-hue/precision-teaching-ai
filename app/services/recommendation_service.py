"""Build transparent, persisted personalized learning plans."""
from sqlalchemy.orm import Session

from app.ai.prerequisite_graph import prerequisites_for
from app.ai.recommender import score_resource
from app.database.seed import leaf_topic_ids
from app.models import LearningResource, LearningSession, Question, Recommendation, Response, Topic
from app.services.adaptive_assessment_service import current_adaptive_difficulty
from app.services.knowledge_service import get_or_create_knowledge_state


def _recent_accuracy(session: Session, student_id: int, topic_id: int) -> float:
    rows = (
        session.query(Response.is_correct)
        .join(Question)
        .filter(Response.student_id == student_id, Question.topic_id == topic_id)
        .order_by(Response.submitted_at.desc())
        .limit(5)
        .all()
    )
    return sum(row[0] for row in rows) / len(rows) if rows else 0.5


def _prerequisite_leaf_topics(
    name: str,
    all_topics: list[Topic],
    leaf_topics: list[Topic],
) -> list[Topic]:
    topic_by_name = {topic.name: topic for topic in all_topics}
    topic_by_id = {topic.id: topic for topic in all_topics}
    topic = topic_by_name.get(name)
    if topic is None:
        return []

    leaf_ids = {leaf.id for leaf in leaf_topics}
    if topic.id in leaf_ids:
        return [topic]

    def is_descendant(candidate: Topic) -> bool:
        parent_id = candidate.parent_topic_id
        while parent_id is not None:
            if parent_id == topic.id:
                return True
            parent = topic_by_id.get(parent_id)
            parent_id = parent.parent_topic_id if parent is not None else None
        return False

    return [leaf for leaf in leaf_topics if is_descendant(leaf)]


def build_learning_path(session: Session, student_id: int, limit: int = 5) -> list[dict]:
    """Persist and return a tailored path, prioritizing weak prerequisites first."""
    all_topics = session.query(Topic).order_by(Topic.id).all()
    leaf_ids = set(leaf_topic_ids(session))
    leaf_topics = [topic for topic in all_topics if topic.id in leaf_ids]
    states = {
        topic.id: get_or_create_knowledge_state(session, student_id, topic.id)
        for topic in leaf_topics
    }
    completed_resource_ids = {
        resource_id
        for (resource_id,) in session.query(Recommendation.resource_id).filter_by(student_id=student_id, completed=True)
    }
    candidates: list[dict] = []
    for topic in leaf_topics:
        state = states[topic.id]
        if state.mastery_probability >= 0.90:
            continue
        weak_prerequisites: list[Topic] = []
        seen_prerequisite_ids: set[int] = set()
        for name in prerequisites_for(topic.name):
            for prerequisite in _prerequisite_leaf_topics(name, all_topics, leaf_topics):
                if prerequisite.id in seen_prerequisite_ids:
                    continue
                seen_prerequisite_ids.add(prerequisite.id)
                if states[prerequisite.id].mastery_probability < 0.70:
                    weak_prerequisites.append(prerequisite)
        target = weak_prerequisites[0] if weak_prerequisites else topic
        target_state = states[target.id]
        desired_difficulty = current_adaptive_difficulty(session, student_id, target.id)
        resources = session.query(LearningResource).filter_by(topic_id=target.id).all()
        for resource in resources:
            result = score_resource(
                mastery=target_state.mastery_probability,
                prerequisite_relevance=1.0 if weak_prerequisites else 0.25,
                difficulty_match=1.0 if resource.difficulty == desired_difficulty else 0.35,
                recent_performance=_recent_accuracy(session, student_id, target.id),
                resource_freshness=0.0 if resource.id in completed_resource_ids else 1.0,
            )
            candidates.append({"topic": target, "resource": resource, "state": target_state, "difficulty": desired_difficulty, "result": result})

    best_by_topic: dict[int, dict] = {}
    for candidate in candidates:
        topic_id = candidate["topic"].id
        if topic_id not in best_by_topic or candidate["result"].score > best_by_topic[topic_id]["result"].score:
            best_by_topic[topic_id] = candidate
    path = sorted(best_by_topic.values(), key=lambda item: item["result"].score, reverse=True)[:limit]

    in_progress_resource_ids = {
        resource_id
        for (resource_id,) in session.query(LearningSession.resource_id).filter_by(
            student_id=student_id, completed_at=None
        )
    }
    stale_recommendations = session.query(Recommendation).filter_by(student_id=student_id, completed=False)
    if in_progress_resource_ids:
        stale_recommendations = stale_recommendations.filter(
            ~Recommendation.resource_id.in_(in_progress_resource_ids)
        )
    stale_recommendations.delete(synchronize_session=False)

    active_keys = {
        (recommendation.topic_id, recommendation.resource_id)
        for recommendation in session.query(Recommendation).filter_by(student_id=student_id, completed=False)
    }
    for item in path:
        key = (item["topic"].id, item["resource"].id)
        if key in active_keys:
            continue
        session.add(Recommendation(
            student_id=student_id, topic_id=item["topic"].id, resource_id=item["resource"].id,
            reason=item["result"].reason, priority=item["result"].priority, score=item["result"].score,
        ))
        active_keys.add(key)
    session.flush()
    return [
        {"topic": item["topic"].name, "topic_id": item["topic"].id, "mastery": item["state"].mastery_probability,
         "priority": item["result"].priority, "reason": item["result"].reason, "difficulty": item["difficulty"],
         "resource_id": item["resource"].id, "resource_title": item["resource"].title,
         "estimated_minutes": item["resource"].estimated_minutes}
        for item in path
    ]
