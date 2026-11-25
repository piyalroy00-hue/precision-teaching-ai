"""Assign the admin role to an existing account without exposing credentials."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.db import get_session
from app.models import User


def main() -> None:
    email = input("Email of existing account to promote: ").strip().lower()
    with get_session() as session:
        user = session.query(User).filter_by(email=email).one_or_none()
        if user is None:
            raise SystemExit("No user exists with that email address.")
        user.role = "admin"
    print(f"Assigned the admin role to {email}.")


if __name__ == "__main__":
    main()