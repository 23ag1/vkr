"""Add briefing_type to modules

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-05-16 02:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a1b2c3"
down_revision: Union[str, None] = "c3d4e5f6a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "modules",
        sa.Column("briefing_type", sa.String(20), nullable=False, server_default="none"),
    )


def downgrade() -> None:
    op.drop_column("modules", "briefing_type")
