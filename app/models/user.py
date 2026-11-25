from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    assessments = relationship("Assessment", back_populates="student")
    responses = relationship("Response", back_populates="student")
    knowledge_states = relationship("KnowledgeState", back_populates="student")
    recommendations = relationship("Recommendation", back_populates="student")
    learning_sessions = relationship("LearningSession", back_populates="student")
    mastery_snapshots = relationship("MasterySnapshot", back_populates="student")
    ai_sessions = relationship("AISession", back_populates="student")
