from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.models.opportunity import (
    Opportunity,
    OpportunityEvidence,
    OpportunityFeedback,
    OpportunityHistory,
    OpportunityRecommendation,
    OpportunityTimeline,
)
from app.repositories.opportunity import OpportunityRepository
from opportunity_engine import OpportunityPipeline


class OpportunityService:
    def __init__(
        self,
        repository: OpportunityRepository,
        pipeline: OpportunityPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or OpportunityPipeline()

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        inputs = await self.repository.pending_company_inputs(limit=limit)
        for item in inputs:
            decision = self.pipeline.process(item)
            await self.repository.store_decision(decision)
            processed += 1
        return {"processed": processed}

    async def list_opportunities(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[Opportunity]:
        return list(await self.repository.list_opportunities(status=status, limit=limit, offset=offset))

    async def get_opportunity(self, opportunity_id: UUID) -> Opportunity | None:
        return await self.repository.get_opportunity(opportunity_id)

    async def history(self, opportunity_id: UUID) -> list[OpportunityHistory]:
        return list(await self.repository.history(opportunity_id))

    async def evidence(self, opportunity_id: UUID) -> list[OpportunityEvidence]:
        return list(await self.repository.evidence(opportunity_id))

    async def timeline(self, opportunity_id: UUID) -> list[OpportunityTimeline]:
        return list(await self.repository.timeline(opportunity_id))

    async def recommendation(self, opportunity_id: UUID) -> OpportunityRecommendation | None:
        return await self.repository.recommendation(opportunity_id)

    async def statistics(self) -> dict[str, float | int | str]:
        since = datetime.now(UTC) - timedelta(days=1)
        return {**await self.repository.statistics(since=since), "window": "24h"}

    async def feedback(
        self,
        *,
        opportunity_id: UUID,
        reviewer: str,
        review_outcome: str,
        corrected_fields: dict[str, Any],
        outcome_label: str | None,
        notes: str | None,
    ) -> OpportunityFeedback:
        return await self.repository.add_feedback(
            opportunity_id=opportunity_id,
            reviewer=reviewer,
            review_outcome=review_outcome,
            corrected_fields=corrected_fields,
            outcome_label=outcome_label,
            notes=notes,
        )
