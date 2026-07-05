"""add_avatar_url_to_users — merge both heads

Revision ID: b2c3d4e5f6a7
Revises: a94297fba62e, c7d8e9f0a1b2
Create Date: 2026-06-13 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = ('a94297fba62e', 'c7d8e9f0a1b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
