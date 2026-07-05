"""add_enterprise_plan_enum

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE planenum ADD VALUE 'enterprise'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum.
    # To downgrade, you would need to create a new type without 'enterprise',
    # alter columns to use the new type, and drop the old type.
    # For simplicity, downgrade is a no-op.
    pass
