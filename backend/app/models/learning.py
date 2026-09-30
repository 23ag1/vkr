import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserModuleProgress(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user_module_progress"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_user_module"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="not_started"
    )  # not_started | in_progress | completed
    score: Mapped[int | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
