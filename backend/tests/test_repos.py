import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository
from src.repositories.url_repository import URLRepository
from src.repositories.workspace_repository import WorkspaceRepository
from src.models.url import URLStatus


@pytest.mark.asyncio
async def test_user_repo_create_and_get(db: AsyncSession, test_user):
    repo = UserRepository(db)
    user = await repo.get(test_user.id)
    assert user is not None
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_user_repo_get_by_email(db: AsyncSession, test_user):
    repo = UserRepository(db)
    user = await repo.get_by_email(test_user.email)
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_user_repo_email_exists(db: AsyncSession, test_user):
    repo = UserRepository(db)
    assert await repo.email_exists(test_user.email) is True
    assert await repo.email_exists("nonexistent@example.com") is False


@pytest.mark.asyncio
async def test_url_repo_create_and_get(db: AsyncSession, test_url):
    repo = URLRepository(db)
    url = await repo.get(test_url.id)
    assert url is not None
    assert url.short_code == "test123"


@pytest.mark.asyncio
async def test_url_repo_get_by_short_code(db: AsyncSession, test_url):
    repo = URLRepository(db)
    url = await repo.get_by_short_code("test123")
    assert url is not None
    assert url.id == test_url.id


@pytest.mark.asyncio
async def test_url_repo_alias_exists(db: AsyncSession, test_url):
    repo = URLRepository(db)
    assert await repo.alias_exists("test123") is True
    assert await repo.alias_exists("nonexistent") is False


@pytest.mark.asyncio
async def test_url_repo_get_workspace_urls(db: AsyncSession, test_url):
    repo = URLRepository(db)
    urls = await repo.get_workspace_urls(workspace_id=test_url.workspace_id, user_id=test_url.user_id)
    assert len(urls) >= 1
    assert urls[0].id == test_url.id


@pytest.mark.asyncio
async def test_url_repo_soft_delete(db: AsyncSession, test_url):
    repo = URLRepository(db)
    await repo.soft_delete(test_url.id)
    url = await repo.get(test_url.id)
    assert url.status == URLStatus.deleted


@pytest.mark.asyncio
async def test_workspace_repo_create_and_get(db: AsyncSession, test_user, test_workspace):
    repo = WorkspaceRepository(db)
    ws = await repo.get(test_workspace.id)
    assert ws is not None
    assert ws.name == "Test Workspace"


@pytest.mark.asyncio
async def test_workspace_repo_get_user_workspaces(db: AsyncSession, test_user, test_workspace):
    repo = WorkspaceRepository(db)
    workspaces = await repo.get_user_workspaces(test_user.id)
    assert len(workspaces) >= 1
    assert test_workspace.id in [w.id for w in workspaces]


@pytest.mark.asyncio
async def test_workspace_repo_create_default(db: AsyncSession, test_user):
    repo = WorkspaceRepository(db)
    ws = await repo.create_default(test_user.id)
    assert ws.name == "Default Workspace"
    assert ws.owner_id == test_user.id
