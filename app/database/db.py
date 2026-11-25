"""SQLAlchemy engine, session factory, and declarative base."""
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine_options = (
    {"connect_args": {"check_same_thread": False}}
    if DATABASE_URL.startswith("sqlite")
    else {}
)
engine = create_engine(DATABASE_URL, **engine_options)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    if engine.dialect.name != "sqlite":
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()
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
