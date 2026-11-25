"""Student registration and login (PBKDF2 password hashing, no plaintext storage)."""
from sqlalchemy.orm import Session

from app.models import User
from app.utils.security import hash_password, verify_password


class AuthError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_student(
    session: Session,
    student_code: str,
    name: str,
    email: str,
    password: str,
    department: str | None = None,
    semester: int | None = None,
) -> User:
    email = normalize_email(email)
    if session.query(User).filter_by(email=email).first() is not None:
        raise AuthError(f"An account with email '{email}' already exists.")
    if session.query(User).filter_by(student_code=student_code).first() is not None:
        raise AuthError(f"Student code '{student_code}' is already registered.")

    user = User(
        student_code=student_code,
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="student",
        department=department,
        semester=semester,
    )
    session.add(user)
    session.commit()
    return user


def authenticate(session: Session, email: str, password: str) -> User:
    user = session.query(User).filter_by(email=normalize_email(email)).one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password.")
    return user
