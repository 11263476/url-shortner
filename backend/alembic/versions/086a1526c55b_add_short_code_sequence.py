"""add_short_code_sequence

Revision ID: 086a1526c55b
Revises: a94297fba62e
Create Date: 2026-06-09 11:36:30.109028

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '086a1526c55b'
down_revision: Union[str, Sequence[str], None] = 'a94297fba62e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sequence for deterministic short code generation
    op.execute("CREATE SEQUENCE IF NOT EXISTS url_short_code_seq START 1000000")


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS url_short_code_seq")
