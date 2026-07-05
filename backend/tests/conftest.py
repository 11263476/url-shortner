from unittest.mock import AsyncMock, patch

import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.security import hash_password
from src.models.url import URL, URLStatus
from src.models.user import User
from src.models.workspace import Workspace
from src.models.workspace_invite import WorkspaceInvite
from src.models.workspace_member import WorkspaceMember

_test_engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=False,
    poolclass=NullPool,
)


@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    """Remove test data before each test to prevent UniqueViolationError."""
    conn = await _test_engine.connect()
    try:
        session = AsyncSession(bind=conn, expire_on_commit=False)
        await session.execute(delete(URL).where(URL.short_code.in_(["test123", "routetest"])))
        await session.execute(delete(WorkspaceInvite))
        await session.execute(delete(WorkspaceMember))
        await session.execute(
            delete(Workspace).where(Workspace.name.in_(["Test Workspace", "Route Test Workspace", "Personal Workspace"]))
        )
        await session.execute(delete(User).where(User.email.like("%@example.com")))
        await session.commit()
        await session.close()
    finally:
        await conn.close()
    yield


@pytest_asyncio.fixture
async def db():
    conn = await _test_engine.connect()
    await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False, autoflush=False)
    yield session
    await session.close()
    await conn.rollback()
    await conn.close()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession):
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_workspace(db: AsyncSession, test_user: User):
    ws = Workspace(name="Test Workspace", owner_id=test_user.id)
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    return ws


@pytest_asyncio.fixture
async def test_url(db: AsyncSession, test_user: User, test_workspace: Workspace):
    url = URL(
        short_code="test123",
        original_url="https://example.com",
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        status=URLStatus.active,
    )
    db.add(url)
    await db.flush()
    await db.refresh(url)
    return url


@pytest_asyncio.fixture(autouse=True)
async def mock_external_services():
    with patch("src.services.auth_service.redis_client", AsyncMock()), \
         patch("src.services.auth_service.EmailService.send_verification_email", AsyncMock()), \
         patch("src.services.auth_service.EmailService.send_password_reset", AsyncMock()), \
         patch("src.services.url_service.delete_url_cache", AsyncMock()), \
         patch("src.services.url_service.EventDispatcher", AsyncMock()), \
         patch("src.services.workspace_service.AuditService", AsyncMock()), \
         patch("src.services.workspace_service.WebhookService", AsyncMock()):
        yield


@pytest_asyncio.fixture
async def mock_repos():
    from src.repositories.folder_repository import FolderRepository
    from src.repositories.tag_repository import TagRepository
    from src.repositories.url_repository import URLRepository
    from src.repositories.user_repository import UserRepository
    from src.repositories.workspace_invite_repository import WorkspaceInviteRepository
    from src.repositories.workspace_member_repository import WorkspaceMemberRepository
    from src.repositories.workspace_repository import WorkspaceRepository

    class MockRepos:
        user_repo = AsyncMock(spec=UserRepository)
        url_repo = AsyncMock(spec=URLRepository)
        workspace_repo = AsyncMock(spec=WorkspaceRepository)
        folder_repo = AsyncMock(spec=FolderRepository)
        tag_repo = AsyncMock(spec=TagRepository)
        member_repo = AsyncMock(spec=WorkspaceMemberRepository)
        invite_repo = AsyncMock(spec=WorkspaceInviteRepository)

    return MockRepos()


@pytest_asyncio.fixture
async def mock_audit():
    from src.services.audit_service import AuditService
    return AsyncMock(spec=AuditService)


@pytest_asyncio.fixture
async def mock_webhooks():
    from src.services.webhook_service import WebhookService
    return AsyncMock(spec=WebhookService)


@pytest_asyncio.fixture
async def mock_event_dispatcher():
    from src.services.event_dispatcher import EventDispatcher
    mock = AsyncMock(spec=EventDispatcher)
    return mock
