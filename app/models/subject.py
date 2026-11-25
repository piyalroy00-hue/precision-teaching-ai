from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)

    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="subject")
