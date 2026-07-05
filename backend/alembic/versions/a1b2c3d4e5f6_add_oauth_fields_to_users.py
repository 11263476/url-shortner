"""add_oauth_fields_to_users

Revision ID: a1b2c3d4e5f6
Revises: 93162d97eb99
Create Date: 2024-12-20 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '93162d97eb99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add OAuth fields."""
    # Add OAuth fields to users table
    op.add_column('users', sa.Column('google_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_provider', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_avatar_url', sa.String(), nullable=True))

    # Create unique index on google_id
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraint
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')

    # Drop OAuth fields
    op.drop_column('users', 'oauth_avatar_url')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'google_id')
