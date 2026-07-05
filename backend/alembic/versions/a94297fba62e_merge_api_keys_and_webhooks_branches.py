"""merge api_keys and webhooks branches

Revision ID: a94297fba62e
Revises: 7b81d53b6f85, f1e2d3c4b5a6
Create Date: 2026-06-08 14:12:10.796230

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'a94297fba62e'
down_revision: Union[str, Sequence[str], None] = ('7b81d53b6f85', 'f1e2d3c4b5a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
