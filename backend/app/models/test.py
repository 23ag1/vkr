import uuid

from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Question(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    module_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")


class UserAnswer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user_answers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
