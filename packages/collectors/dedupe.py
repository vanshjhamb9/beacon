from redis.asyncio import Redis


class RedisDedupeStore:
    def __init__(self, redis: Redis, *, namespace: str = "collectors:dedupe") -> None:
        self.redis = redis
        self.namespace = namespace

    async def mark_new(self, idempotency_key: str, *, ttl_seconds: int = 604_800) -> bool:
        key = f"{self.namespace}:{idempotency_key}"
        return bool(await self.redis.set(key, "1", nx=True, ex=ttl_seconds))
