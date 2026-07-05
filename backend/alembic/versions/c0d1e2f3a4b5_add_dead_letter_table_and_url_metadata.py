"""add_dead_letter_table_and_url_metadata

Revision ID: c0d1e2f3a4b5
Revises: a4b5c6d7e8f9
Create Date: 2026-06-21 19:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = 'c0d1e2f3a4b5'
down_revision: Union[str, Sequence[str], None] = 'a4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dead_letter_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('event_key', sa.String(), nullable=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('error', sa.String(), nullable=False),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
    )
    op.add_column('urls', sa.Column('title', sa.String(), nullable=True))
    op.add_column('urls', sa.Column('description', sa.String(), nullable=True))
    op.add_column('urls', sa.Column('og_image', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('urls', 'og_image')
    op.drop_column('urls', 'description')
    op.drop_column('urls', 'title')
    op.drop_table('dead_letter_events')
