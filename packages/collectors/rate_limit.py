from redis.asyncio import Redis


class RedisRateLimiter:
    def __init__(self, redis: Redis, *, namespace: str = "collectors:rate-limit") -> None:
        self.redis = redis
        self.namespace = namespace

    async def allow(self, source: str, *, limit: int, window_seconds: int = 60) -> bool:
        key = f"{self.namespace}:{source}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, window_seconds)
        return int(count) <= limit
