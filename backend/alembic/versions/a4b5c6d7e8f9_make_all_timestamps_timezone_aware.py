"""make_all_timestamps_timezone_aware

Revision ID: a4b5c6d7e8f9
Revises: b88b76ab784a
Create Date: 2026-06-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, Sequence[str], None] = 'b88b76ab784a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = {
    "users": ["created_at"],
    "urls": ["created_at", "expires_at"],
    "url_analytics_summary": ["last_clicked_at"],
    "api_keys": ["created_at", "expires_at", "last_used_at"],
    "favorites": ["created_at"],
    "folders": ["created_at"],
    "webhooks": ["created_at"],
    "webhook_events": ["created_at"],
    "webhook_received_events": ["created_at"],
    "workspaces": ["created_at"],
    "workspace_invites": ["created_at", "expires_at"],
    "workspace_members": ["joined_at"],
}


def upgrade() -> None:
    for table, columns in TABLES.items():
        for col in columns:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    for table, columns in TABLES.items():
        for col in columns:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TIMESTAMP WITHOUT TIME ZONE")
