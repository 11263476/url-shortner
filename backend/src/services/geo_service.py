"""IP geolocation service using ip-api.com with Redis caching."""
from urllib.parse import urlencode

import httpx

from src.core.redis import redis_client


class GeoService:
    CACHE_TTL = 86400  # 24 hours

    async def resolve(self, ip: str) -> dict:
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            return {"country": None, "city": None}

        cache_key = f"geo:{ip}"
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                import json
                return json.loads(cached)  # type: ignore[no-any-return]

        try:
            params = urlencode({"fields": "country,city,query"})
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"http://ip-api.com/json/{ip}?{params}")
                data = resp.json()
        except Exception:
            return {"country": None, "city": None}

        result = {
            "country": data.get("country"),
            "city": data.get("city"),
        }

        if redis_client and result["country"]:
            import json
            await redis_client.setex(cache_key, self.CACHE_TTL, json.dumps(result))

        return result
