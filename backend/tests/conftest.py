import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.workspace import Workspace
from src.models.url import URL, URLStatus
from src.core.security import hash_password


@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db: AsyncSession):
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_workspace(db: AsyncSession, test_user: User):
    ws = Workspace(name="Test Workspace", owner_id=test_user.id)
    db.add(ws)
    await db.commit()
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
    await db.commit()
    await db.refresh(url)
    return url


@pytest.fixture(autouse=True)
def mock_external_services():
    with patch("src.services.auth_service.redis_client", AsyncMock()), \
         patch("src.services.url_service.publish_event", AsyncMock()), \
         patch("src.services.url_service.delete_url_cache", AsyncMock()), \
         patch("src.services.workspace_service.publish_event", AsyncMock()):
        yield
