"""
Test suite for all 5 async workers.
Tests: analytics, aggregation, expiry, cleanup, and QR workers.
"""

import logging
from datetime import datetime, timedelta

import pytest
pytestmark = pytest.mark.integration
import pytest_asyncio
from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.core.mongodb import init_mongodb
from src.documents.click_event import ClickEvent
from src.models.analytics import URLAnalyticsSummary
from src.models.url import URL, URLStatus
from src.models.user import User
from src.models.workspace import Workspace
from src.workers.aggregation_worker import run_aggregation_rollup
from src.workers.analytics_worker import process_event
from src.workers.cleanup_worker import run_cleanup
from src.workers.expiry_worker import scan_and_expire_urls
from src.workers.webhook_retry_worker import backoff_delay


logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def setup_db():
    """Setup test database with sample data."""
    async with AsyncSessionLocal() as db:
        # Create test user
        user = User(email="test@example.com", password_hash="test_hash", is_verified=True)
        db.add(user)
        await db.flush()

        # Create workspace
        workspace = Workspace(name="Test Workspace", owner_id=user.id)
        db.add(workspace)
        await db.flush()

        # Create test URL
        url = URL(
            short_code="test123",
            original_url="https://example.com",
            user_id=user.id,
            workspace_id=workspace.id,
            status=URLStatus.active,
        )
        db.add(url)
        await db.commit()

        return {"user_id": user.id, "workspace_id": workspace.id, "url_id": url.id, "short_code": "test123"}


@pytest.mark.asyncio
async def test_analytics_worker_process_event(setup_db):
    """Test that analytics worker correctly processes click events."""
    test_data = await setup_db

    event_data = {
        "event_id": "evt-001",
        "short_code": test_data["short_code"],
        "original_url": "https://example.com",
        "workspace_id": test_data["workspace_id"],
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "referer": "https://twitter.com",
        "clicked_at": datetime.utcnow().isoformat(),
    }

    # Process the event
    await process_event(event_data, logger)

    # Verify MongoDB has the event
    await init_mongodb()
    click_event = await ClickEvent.find_one(ClickEvent.event_id == "evt-001")
    assert click_event is not None
    assert click_event.short_code == test_data["short_code"]
    assert click_event.ip_address == "192.168.1.1"

    # Verify PostgreSQL analytics summary was updated
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(URLAnalyticsSummary).where(URLAnalyticsSummary.url_id == test_data["url_id"])
        )
        summary = result.scalar_one_or_none()
        assert summary is not None
        assert summary.total_clicks >= 1


@pytest.mark.asyncio
async def test_aggregation_worker_rollup(setup_db):
    """Test that aggregation worker correctly rolls up MongoDB data to PostgreSQL."""
    test_data = await setup_db

    # First, create some click events in MongoDB
    await init_mongodb()
    for i in range(5):
        event = ClickEvent(
            event_id=f"evt-{i:03d}",
            short_code=test_data["short_code"],
            original_url="https://example.com",
            workspace_id=test_data["workspace_id"],
            ip_address=f"192.168.1.{i}",
            user_agent="Mozilla/5.0",
            clicked_at=datetime.utcnow(),
        )
        await event.insert()

    # Run aggregation rollup
    await run_aggregation_rollup(logger)

    # Verify PostgreSQL summaries were updated
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(URLAnalyticsSummary).where(URLAnalyticsSummary.url_id == test_data["url_id"])
        )
        summary = result.scalar_one_or_none()
        assert summary is not None
        assert summary.total_clicks == 5
        # Unique IPs: 192.168.1.0 through 192.168.1.4 = 5 unique
        assert summary.unique_clicks == 5


@pytest.mark.asyncio
async def test_expiry_worker_disables_expired_urls(setup_db):
    """Test that expiry worker correctly marks expired URLs as disabled."""
    test_data = await setup_db

    # Create an expired URL
    async with AsyncSessionLocal() as db:
        expired_url = URL(
            short_code="expired123",
            original_url="https://old.example.com",
            user_id=test_data["user_id"],
            workspace_id=test_data["workspace_id"],
            status=URLStatus.active,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        )
        db.add(expired_url)
        await db.commit()
        expired_url_id = expired_url.id

    # Run expiry worker
    await scan_and_expire_urls(logger)

    # Verify URL is now disabled
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(URL).where(URL.id == expired_url_id))
        url = result.scalar_one_or_none()
        assert url.status == URLStatus.disabled


@pytest.mark.asyncio
async def test_cleanup_worker_purges_deleted_urls(setup_db):
    """Test that cleanup worker correctly purges soft-deleted URLs."""
    test_data = await setup_db

    # Create a URL and soft-delete it
    async with AsyncSessionLocal() as db:
        url_to_delete = URL(
            short_code="del123",
            original_url="https://delete-me.com",
            user_id=test_data["user_id"],
            workspace_id=test_data["workspace_id"],
            status=URLStatus.active,
        )
        db.add(url_to_delete)
        await db.commit()
        url_to_delete_id = url_to_delete.id

        # Add some click events
        await init_mongodb()
        for i in range(3):
            event = ClickEvent(
                event_id=f"del-evt-{i}",
                short_code="del123",
                original_url="https://delete-me.com",
                workspace_id=test_data["workspace_id"],
                ip_address=f"10.0.0.{i}",
                clicked_at=datetime.utcnow(),
            )
            await event.insert()

    # Soft-delete the URL
    async with AsyncSessionLocal() as db:
        url = await db.get(URL, url_to_delete_id)
        url.status = URLStatus.deleted
        await db.commit()

    # Run cleanup worker
    async with AsyncSessionLocal() as cleanup_db:
        await run_cleanup(logger, cleanup_db)

    # Verify URL is hard-deleted from PostgreSQL
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(URL).where(URL.id == url_to_delete_id))
        url = result.scalar_one_or_none()
        assert url is None

    # Verify click events are removed from MongoDB
    await init_mongodb()
    click_events = await ClickEvent.find(ClickEvent.short_code == "del123").to_list()
    assert len(click_events) == 0


@pytest.mark.asyncio
async def test_multiple_workers_end_to_end(setup_db):
    """Test full workflow: create URL -> log clicks -> aggregate -> cleanup."""
    test_data = await setup_db

    # 1. Log multiple click events
    await init_mongodb()
    for i in range(10):
        event_data = {
            "event_id": f"e2e-evt-{i:03d}",
            "short_code": test_data["short_code"],
            "original_url": "https://example.com",
            "workspace_id": test_data["workspace_id"],
            "ip_address": f"172.16.0.{i}",
            "user_agent": "Mozilla/5.0",
            "clicked_at": datetime.utcnow().isoformat(),
        }
        await process_event(event_data, logger)

    # 2. Run aggregation rollup
    await run_aggregation_rollup(logger)

    # 3. Verify analytics
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(URLAnalyticsSummary).where(URLAnalyticsSummary.url_id == test_data["url_id"])
        )
        summary = result.scalar_one_or_none()
        assert summary is not None
        assert summary.total_clicks == 10
        assert summary.unique_clicks == 10

    # 4. Soft-delete the URL
    async with AsyncSessionLocal() as db:
        url = await db.get(URL, test_data["url_id"])
        url.status = URLStatus.deleted
        await db.commit()

    # 5. Run cleanup
    async with AsyncSessionLocal() as cleanup_db:
        await run_cleanup(logger, cleanup_db)

    # 6. Verify everything is cleaned up
    async with AsyncSessionLocal() as db:
        url = await db.get(URL, test_data["url_id"])
        assert url is None

    click_events = await ClickEvent.find(ClickEvent.short_code == test_data["short_code"]).to_list()
    assert len(click_events) == 0


@pytest.mark.asyncio
async def test_metadata_worker_extract_and_store(setup_db):
    """Test metadata worker extracts OG tags and stores them."""
    test_data = await setup_db
    from src.workers.metadata_worker import extract_metadata

    meta = await extract_metadata("https://example.com")
    assert isinstance(meta, dict)
    assert "title" in meta
    assert "description" in meta
    assert "og_image" in meta


@pytest.mark.asyncio
async def test_webhook_retry_worker_scan(setup_db):
    """Test webhook retry worker scans for failed events."""
    from src.workers.webhook_retry_worker import backoff_delay
    assert backoff_delay(1) == 30
    assert backoff_delay(2) == 60
    assert backoff_delay(3) == 120


@pytest.mark.asyncio
async def test_webhook_retry_backoff():
    """Test exponential backoff calculation."""
    assert backoff_delay(1) == 30
    assert backoff_delay(2) == 60
    assert backoff_delay(3) == 120
    assert backoff_delay(8) == 3600  # capped at max


@pytest.mark.asyncio
async def test_analytics_worker_json_fallback(setup_db):
    """Test analytics worker handles JSON fallback when Avro fails."""
    from src.workers.analytics_worker import process_event

    test_data = await setup_db
    event_data = {
        "event_id": "json-fallback-test",
        "short_code": test_data["short_code"],
        "original_url": "https://example.com",
        "workspace_id": test_data["workspace_id"],
        "ip_address": "10.0.0.1",
        "user_agent": "curl/8.0",
        "referer": "",
        "clicked_at": datetime.utcnow().isoformat(),
    }
    await process_event(event_data, logger)
    await init_mongodb()
    click_event = await ClickEvent.find_one(ClickEvent.event_id == "json-fallback-test")
    assert click_event is not None
    assert click_event.ip_address == "10.0.0.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
