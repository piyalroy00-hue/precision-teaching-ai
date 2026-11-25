"""SQLAlchemy engine, session factory, and declarative base."""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# expire_on_commit=False: callers often read attributes from ORM objects after the
# `with get_session()` block has committed/closed. Without this, SQLAlchemy would
# try to lazily re-fetch expired attributes on a now-closed session and raise a
# DetachedInstanceError while rendering templates or processing request data.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create all tables that don't already exist."""
    import app.models  # noqa: F401 - ensures all models are registered on Base

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context-managed session: commits on success, rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
