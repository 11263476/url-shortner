import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.concurrency,
]


class TestConcurrentRequests:
    @pytest.mark.asyncio
    async def test_health_endpoint_under_concurrent_load(self, app):
        transport = ASGITransport(app=app)

        async def hit_health():
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                return await ac.get("/health")

        results = await asyncio.gather(*[hit_health() for _ in range(20)], return_exceptions=True)
        successes = [r for r in results if not isinstance(r, Exception) and r.status_code == 200]
        assert len(successes) >= 18, f"Only {len(successes)} of 20 health checks succeeded"

    @pytest.mark.asyncio
    async def test_concurrent_redirect_no_crash(self, app):
        transport = ASGITransport(app=app)

        async def get_nonexistent():
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                return await ac.get("/nonexistent")

        results = await asyncio.gather(*[get_nonexistent() for _ in range(10)], return_exceptions=True)
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) == 10
