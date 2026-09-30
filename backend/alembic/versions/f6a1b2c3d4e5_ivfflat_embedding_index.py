"""Add ivfflat cosine index on document_chunks.embedding

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Branch Labels: None
Depends On: None

Per CLAUDE.md: vector similarity search uses the pgvector `<=>` (cosine distance)
operator, so the index must use `vector_cosine_ops` with lists=100.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f6a1b2c3d4e5"
down_revision: Union[str, None] = "e5f6a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_document_chunks_embedding"


def upgrade() -> None:
    # ivfflat builds centroids from existing rows at CREATE time. On an empty or
    # newly bulk-loaded table the index should be rebuilt (REINDEX) after ingestion
    # for good recall. lists=100 suits the prototype scale (~thousands of chunks);
    # tune toward rows/1000 as the corpus grows.
    op.create_index(
        INDEX_NAME,
        "document_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="document_chunks")
