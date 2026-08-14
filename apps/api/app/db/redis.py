from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


def create_redis_client() -> Redis:
    """Create a Redis client bound to the current event loop."""
    settings = get_settings()
    return Redis.from_url(settings.redis_dsn, encoding="utf-8", decode_responses=True)


@lru_cache
def get_redis_client() -> Redis:
    """Cached client for the long-lived API process event loop."""
    return create_redis_client()


async def close_redis() -> None:
    client = get_redis_client()
    await client.aclose()
    get_redis_client.cache_clear()
