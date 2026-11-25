"""Administrative user maintenance with explicit dependent-record cleanup."""
from sqlalchemy.orm import Session

from app.models import (
    AIMessage,
    AISession,
    Assessment,
    GeneratedContent,
    KnowledgeState,
    LearningSession,
    MasterySnapshot,
    Recommendation,
    Response,
    User,
)
from app.utils.security import hash_password


def list_users(session: Session) -> list[User]:
    """Return user records for administration; callers must not expose password hashes."""
    return session.query(User).order_by(User.created_at.desc()).all()


def delete_user(session: Session, user_id: int, administrator_id: int) -> None:
    """Permanently remove a user and associated learning data, excluding self-deletion."""
    if user_id == administrator_id:
        raise ValueError("Administrators cannot remove their own account.")
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("User does not exist.")

    ai_session_ids = [session_id for (session_id,) in session.query(AISession.id).filter_by(student_id=user_id)]
    if ai_session_ids:
        session.query(AIMessage).filter(AIMessage.session_id.in_(ai_session_ids)).delete(synchronize_session=False)
    session.query(AISession).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(GeneratedContent).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(MasterySnapshot).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(Recommendation).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(LearningSession).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(Response).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(KnowledgeState).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.query(Assessment).filter_by(student_id=user_id).delete(synchronize_session=False)
    session.delete(user)
    session.flush()


def reset_user_password(session: Session, user_id: int, new_password: str) -> None:
    """Store a replacement password hash; plaintext passwords are never persisted."""
    if len(new_password) < 8:
        raise ValueError("The new password must contain at least 8 characters.")
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("User does not exist.")
    user.password_hash = hash_password(new_password)
    session.flush()