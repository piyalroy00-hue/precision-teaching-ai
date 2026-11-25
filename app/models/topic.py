from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    parent_topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    subject = relationship("Subject", back_populates="topics")
    parent = relationship("Topic", remote_side=[id], backref="children")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="topic")
    learning_resources = relationship("LearningResource", back_populates="topic")
    recommendations = relationship("Recommendation", back_populates="topic")
    learning_sessions = relationship("LearningSession", back_populates="topic")
    mastery_snapshots = relationship("MasterySnapshot", back_populates="topic")
    ai_sessions = relationship("AISession", back_populates="topic")
