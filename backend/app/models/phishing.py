import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PhishingTemplate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "phishing_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # easy | medium | hard


class PhishingCampaign(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "phishing_campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phishing_templates.id", ondelete="RESTRICT"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft | active | completed
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PhishingRecipient(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "phishing_recipients"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phishing_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tracking_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
