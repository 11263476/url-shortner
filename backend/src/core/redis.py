import json
import time

from upstash_redis.asyncio import Redis as UpstashRedis

from src.core.config import settings


class UpstashRedisAdapter:
    def __init__(self, url: str, token: str):
        self._client = UpstashRedis(url=url, token=token)

    async def ping(self):
        return await self._client.ping()

    async def get(self, key: str):
        return await self._client.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        return await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str):
        return await self._client.delete(key)

    async def incr(self, key: str):
        return await self._client.incr(key)

    async def expire(self, key: str, ttl: int):
        return await self._client.expire(key, ttl)

    async def eval(self, script: str, numkeys: int, *args):
        cmd = ["EVAL", script, str(numkeys)] + list(args)
        return await self._client.execute(cmd)


redis_client: UpstashRedisAdapter = UpstashRedisAdapter(
    url=settings.UPSTASH_REDIS_REST_URL or "",
    token=settings.UPSTASH_REDIS_REST_TOKEN or "",
)


async def init_redis():
    """Verify that Redis is connected on startup."""
    try:
        await redis_client.ping()
        print("[REDIS] Redis (Upstash REST) connected successfully.")
    except Exception as e:
        print(f"[REDIS] Redis ping failed: {e}")
        raise
    return redis_client


TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])
local requested = tonumber(ARGV[4] or 1)

local bucket = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(bucket[1])
local last_updated = tonumber(bucket[2])

if not tokens then
    tokens = capacity
    last_updated = current_time
else
    local delta = math.max(0, current_time - last_updated)
    tokens = math.min(capacity, tokens + delta * refill_rate)
end

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', current_time)
    redis.call('EXPIRE', key, 86400)
    return 1
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', current_time)
    redis.call('EXPIRE', key, 86400)
    return 0
end
"""

async def check_rate_limit(key: str, capacity: int, refill_rate_per_sec: float) -> bool:
    now = time.time()
    result = await redis_client.eval(
        TOKEN_BUCKET_LUA,
        1,
        key,
        str(capacity),
        str(refill_rate_per_sec),
        str(now),
        "1"
    )
    return result == 0

async def get_url_cache(short_code: str) -> dict | None:
    data = await redis_client.get(f"url:{short_code}")
    if data:
        try:
            return json.loads(data)
        except Exception:
            return None
    return None

async def set_url_cache(short_code: str, url_data: dict, ttl: int = 86400) -> None:
    await redis_client.setex(f"url:{short_code}", ttl, json.dumps(url_data))

async def delete_url_cache(short_code: str) -> None:
    await redis_client.delete(f"url:{short_code}")
