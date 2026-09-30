import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TrainingSchedule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_schedules"

    action: Mapped[str] = mapped_column(String(50), nullable=False)
    cadence: Mapped[str] = mapped_column(String(20), nullable=False)  # monthly | quarterly | annual
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("modules.id", ondelete="SET NULL"), nullable=True
    )
    target_roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
