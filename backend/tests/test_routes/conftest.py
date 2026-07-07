import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.integration
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.security import hash_password
from src.main import create_app
from src.models.url import URL, URLStatus
from src.models.user import User
from src.models.workspace import Workspace
from src.models.workspace_invite import WorkspaceInvite
from src.models.workspace_member import MemberRole, WorkspaceMember

_test_engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=False,
    poolclass=NullPool,
)


@asynccontextmanager
async def _test_lifespan(app):
    yield


@pytest_asyncio.fixture(autouse=True)
async def patch_async_session_local():
    import src.core.database as db_mod

    original = db_mod.AsyncSessionLocal
    test_session = async_sessionmaker(
        bind=_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    db_mod.AsyncSessionLocal = test_session
    try:
        yield
    finally:
        db_mod.AsyncSessionLocal = original


@pytest_asyncio.fixture(autouse=True)
async def cleanup():
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
    session = AsyncSession(bind=conn, expire_on_commit=False)
    yield session
    await session.close()
    await conn.close()


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
        short_code="routetest",
        original_url="https://example.com/route",
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        status=URLStatus.active,
    )
    db.add(url)
    await db.commit()
    await db.refresh(url)
    return url


@pytest_asyncio.fixture
def app(test_user: User, test_workspace: Workspace, test_url: URL):
    app = create_app(lifespan_override=_test_lifespan)
    return app


@pytest_asyncio.fixture
async def auth_headers(app, test_user: User):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
        data = resp.json()
        token = data["access_token"]
        return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client(app, auth_headers):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=auth_headers) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_member(db: AsyncSession, test_user: User, test_workspace: Workspace):
    member = WorkspaceMember(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        role=MemberRole.admin,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member
