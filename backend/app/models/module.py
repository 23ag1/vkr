from sqlalchemy import ARRAY, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Module(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "modules"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_roles: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    order_index: Mapped[int] = mapped_column(nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(nullable=False, default=False)
    # FSTEC №21 briefing classification: none|introductory|primary|repeated|extraordinary
    briefing_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
