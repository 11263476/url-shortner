"""audit_logs_timezone_aware

Revision ID: b88b76ab784a
Revises: fa956e5f83aa
Create Date: 2026-06-13 18:23:57.478671

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b88b76ab784a'
down_revision: Union[str, Sequence[str], None] = 'fa956e5f83aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE audit_logs ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE audit_logs ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
