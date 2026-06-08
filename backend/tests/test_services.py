import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.services.auth_service import AuthService
from src.services.url_service import URLService
from src.services.workspace_service import WorkspaceService
from src.schemas.url import URLCreate
from src.models.url import URLStatus


@pytest.mark.asyncio
async def test_auth_register_success(db: AsyncSession):
    service = AuthService(db)
    user = await service.register(email="new@example.com", password="newpass123")
    assert user.email == "new@example.com"
    assert user.is_verified is False


@pytest.mark.asyncio
async def test_auth_register_duplicate_email(db: AsyncSession, test_user):
    service = AuthService(db)
    with pytest.raises(HTTPException) as exc:
        await service.register(email=test_user.email, password="newpass123")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_auth_login_success(db: AsyncSession, test_user):
    service = AuthService(db)
    token = await service.login(email=test_user.email, password="testpass123")
    assert token.access_token is not None
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_auth_login_wrong_password(db: AsyncSession, test_user):
    service = AuthService(db)
    with pytest.raises(HTTPException) as exc:
        await service.login(email=test_user.email, password="wrongpass")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_url_create_success(db: AsyncSession, test_user, test_workspace):
    service = URLService(db)
    payload = URLCreate(
        original_url="https://example.com",
        workspace_id=test_workspace.id,
    )
    url = await service.create(payload, user_id=test_user.id)
    assert url.original_url == "https://example.com"
    assert url.workspace_id == test_workspace.id
    assert url.user_id == test_user.id
    assert url.status == URLStatus.active
    assert url.short_code is not None


@pytest.mark.asyncio
async def test_url_create_reserved_alias(db: AsyncSession, test_user, test_workspace):
    service = URLService(db)
    payload = URLCreate(
        original_url="https://example.com",
        workspace_id=test_workspace.id,
        custom_alias="admin",
    )
    with pytest.raises(HTTPException) as exc:
        await service.create(payload, user_id=test_user.id)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_url_get_by_id(db: AsyncSession, test_user, test_url):
    service = URLService(db)
    url = await service.get(id=test_url.id, user_id=test_user.id)
    assert url.id == test_url.id
    assert url.short_code == "test123"


@pytest.mark.asyncio
async def test_url_get_not_found(db: AsyncSession, test_user):
    service = URLService(db)
    with pytest.raises(HTTPException) as exc:
        await service.get(id=99999, user_id=test_user.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_url_delete(db: AsyncSession, test_user, test_url):
    service = URLService(db)
    await service.delete(id=test_url.id, user_id=test_user.id)
    with pytest.raises(HTTPException) as exc:
        await service.get(id=test_url.id, user_id=test_user.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_workspace_create(db: AsyncSession, test_user):
    service = WorkspaceService(db)
    ws = await service.create(name="New Workspace", owner_id=test_user.id)
    assert ws.name == "New Workspace"
    assert ws.owner_id == test_user.id


@pytest.mark.asyncio
async def test_workspace_list(db: AsyncSession, test_user, test_workspace):
    service = WorkspaceService(db)
    workspaces = await service.list(user_id=test_user.id)
    assert len(workspaces) == 1
    assert workspaces[0].id == test_workspace.id
