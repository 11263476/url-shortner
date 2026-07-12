from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


class TestRedisDown:
    @pytest.mark.asyncio
    async def test_health_returns_503_when_redis_unreachable(self, app):
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis unreachable")

        with patch("src.main.redis_client", mock_redis):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "unhealthy"
        assert data["redis"] is False
