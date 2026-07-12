from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


class TestPostgresDown:
    @pytest.mark.asyncio
    async def test_health_returns_503_when_db_unreachable(self, app):
        async def mock_health() -> bool:
            return False

        with patch("src.main.check_db_health", mock_health):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "unhealthy"
        assert data["database"] is False
