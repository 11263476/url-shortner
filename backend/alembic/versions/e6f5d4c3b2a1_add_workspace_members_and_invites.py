"""add_workspace_members_and_invites

Revision ID: e6f5d4c3b2a1
Revises: d1e2f3a4b5c6
Create Date: 2026-06-08 10:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e6f5d4c3b2a1'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('workspace_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('admin', 'editor', 'viewer', name='memberrole'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_workspace_members_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_workspace_members_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_workspace_members')),
        sa.UniqueConstraint('workspace_id', 'user_id', name=op.f('uq_workspace_members_workspace_id_user_id')),
    )
    op.create_index(op.f('ix_workspace_members_id'), 'workspace_members', ['id'], unique=False)

    op.create_table('workspace_invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('invited_by', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'expired', 'cancelled', name='invitestatus'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], name=op.f('fk_workspace_invites_invited_by_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_workspace_invites_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_workspace_invites')),
    )
    op.create_index(op.f('ix_workspace_invites_id'), 'workspace_invites', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_invites_token'), 'workspace_invites', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_workspace_invites_token'), table_name='workspace_invites')
    op.drop_index(op.f('ix_workspace_invites_id'), table_name='workspace_invites')
    op.drop_table('workspace_invites')
    op.drop_index(op.f('ix_workspace_members_id'), table_name='workspace_members')
    op.drop_table('workspace_members')
    sa.Enum(name='memberrole').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='invitestatus').drop(op.get_bind(), checkfirst=False)
