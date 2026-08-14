from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.models.revenue import SalesPlaybook
from app.repositories.revenue import RevenueRepository
from revenue_engine import RevenuePipeline


class RevenueService:
    def __init__(
        self,
        repository: RevenueRepository,
        pipeline: RevenuePipeline | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or RevenuePipeline()

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        inputs = await self.repository.pending_opportunity_inputs(limit=limit)
        for item in inputs:
            recommendation = self.pipeline.process(item)
            await self.repository.store_recommendation(recommendation)
            processed += 1
        return {"processed": processed}

    async def ensure_catalog_seeded(self) -> None:
        await self.repository.ensure_services_seeded()

    async def list_opportunities(
        self,
        *,
        priority: str | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        return list(
            await self.repository.list_opportunities(priority=priority, limit=limit, offset=offset)
        )

    async def company_revenue(self, company_id: UUID) -> dict[str, Any] | None:
        return await self.repository.company_revenue(company_id)

    async def company_playbook(self, company_id: UUID) -> SalesPlaybook | None:
        return await self.repository.company_playbook(company_id)

    async def statistics(self) -> dict[str, float | int | str]:
        since = datetime.now(UTC) - timedelta(days=1)
        return {**await self.repository.statistics(since=since), "window": "24h"}
