import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.middleware.rbac import require_role
from src.models.workspace_member import WorkspaceMember, MemberRole
from src.models.user import User
from src.models.workspace import Workspace


@pytest.mark.asyncio
async def test_require_role_admin(db: AsyncSession, test_user: User, test_workspace: Workspace):
    member = WorkspaceMember(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        role=MemberRole.admin,
    )
    db.add(member)
    await db.commit()

    result = await require_role(workspace_id=test_workspace.id, user_id=test_user.id, min_role=MemberRole.admin)
    assert result is True


@pytest.mark.asyncio
async def test_require_role_editor_has_admin(db: AsyncSession, test_user: User, test_workspace: Workspace):
    member = WorkspaceMember(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        role=MemberRole.admin,
    )
    db.add(member)
    await db.commit()

    result = await require_role(workspace_id=test_workspace.id, user_id=test_user.id, min_role=MemberRole.editor)
    assert result is True


@pytest.mark.asyncio
async def test_require_role_viewer_denied_for_editor(db: AsyncSession, test_user: User, test_workspace: Workspace):
    member = WorkspaceMember(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        role=MemberRole.viewer,
    )
    db.add(member)
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await require_role(workspace_id=test_workspace.id, user_id=test_user.id, min_role=MemberRole.editor)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_role_no_membership(db: AsyncSession, test_workspace: Workspace):
    with pytest.raises(HTTPException) as exc:
        await require_role(workspace_id=test_workspace.id, user_id=99999, min_role=MemberRole.viewer)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_role_hierarchy_admin_greater_than_viewer(db: AsyncSession, test_user: User, test_workspace: Workspace):
    member = WorkspaceMember(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        role=MemberRole.admin,
    )
    db.add(member)
    await db.commit()

    result = await require_role(workspace_id=test_workspace.id, user_id=test_user.id, min_role=MemberRole.viewer)
    assert result is True
