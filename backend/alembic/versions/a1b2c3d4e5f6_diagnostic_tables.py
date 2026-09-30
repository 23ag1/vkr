"""diagnostic tables and user.diagnostic_completed_at

Revision ID: a1b2c3d4e5f6
Revises: febd06a0a434
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'febd06a0a434'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('diagnostic_completed_at', sa.DateTime(timezone=True), nullable=True))

    op.alter_column('questions', 'module_id', nullable=True)

    op.create_table(
        'diagnostic_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('answers', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_finished', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_diagnostic_sessions_user_id', 'diagnostic_sessions', ['user_id'])

    op.create_table(
        'user_competency_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('topic', sa.String(50), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_competency_profiles_user_id', 'user_competency_profiles', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_user_competency_profiles_user_id', table_name='user_competency_profiles')
    op.drop_table('user_competency_profiles')
    op.drop_index('ix_diagnostic_sessions_user_id', table_name='diagnostic_sessions')
    op.drop_table('diagnostic_sessions')
    op.alter_column('questions', 'module_id', nullable=False)
    op.drop_column('users', 'diagnostic_completed_at')
