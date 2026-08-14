from datetime import UTC, datetime

from sqlalchemy import select

from app.models.source_health import SourceHealth, SourceHealthStatus
from app.repositories.base import BaseRepository


class SourceHealthRepository(BaseRepository[SourceHealth]):
    model = SourceHealth

    async def get_by_source(self, source: str) -> SourceHealth | None:
        result = await self.session.execute(
            select(SourceHealth).where(SourceHealth.source == source).limit(1)
        )
        return result.scalar_one_or_none()

    async def record_success(self, source: str, latency_ms: float) -> SourceHealth:
        health = await self.get_by_source(source)
        now = datetime.now(UTC)
        if health is None:
            health = SourceHealth(source=source, consecutive_failures=0)
            self.session.add(health)

        previous_average = health.average_latency_ms
        health.average_latency_ms = (
            latency_ms if previous_average is None else round((previous_average * 0.8) + (latency_ms * 0.2), 2)
        )
        health.status = SourceHealthStatus.HEALTHY
        health.last_success_at = now
        health.last_checked_at = now
        health.last_error = None
        health.consecutive_failures = 0
        await self.session.flush()
        await self.session.refresh(health)
        return health

    async def record_failure(self, source: str, error: str) -> SourceHealth:
        health = await self.get_by_source(source)
        now = datetime.now(UTC)
        if health is None:
            health = SourceHealth(source=source, consecutive_failures=0)
            self.session.add(health)

        failures = int(health.consecutive_failures or 0) + 1
        health.consecutive_failures = failures
        health.status = (
            SourceHealthStatus.DOWN if failures >= 3 else SourceHealthStatus.DEGRADED
        )
        health.last_failure_at = now
        health.last_checked_at = now
        health.last_error = error[:2000]
        await self.session.flush()
        await self.session.refresh(health)
        return health
