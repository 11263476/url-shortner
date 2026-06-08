import redis.asyncio as aioredis
from src.core.config import settings
import time
import json

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)

async def init_redis():
    """Verify that Redis is connected on startup."""
    await redis_client.ping()

# Token Bucket Lua Script
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
    """
    Returns True if rate limited (limit exceeded), False if request is allowed.
    """
    now = time.time()
    result = await redis_client.eval(
        TOKEN_BUCKET_LUA,
        1,  # Number of keys
        key,
        str(capacity),
        str(refill_rate_per_sec),
        str(now),
        "1"
    )
    return result == 0

async def get_url_cache(short_code: str) -> dict | None:
    """Retrieve URL from Redis cache."""
    data = await redis_client.get(f"url:{short_code}")
    if data:
        try:
            return json.loads(data)
        except Exception:
            return None
    return None

async def set_url_cache(short_code: str, url_data: dict, ttl: int = 86400) -> None:
    """Store URL in Redis cache."""
    await redis_client.setex(f"url:{short_code}", ttl, json.dumps(url_data))

async def delete_url_cache(short_code: str) -> None:
    """Invalidate URL cache."""
    await redis_client.delete(f"url:{short_code}")
