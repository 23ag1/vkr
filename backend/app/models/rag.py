import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("modules.id", ondelete="SET NULL"), nullable=True
    )


class DocumentChunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False, default=0)
