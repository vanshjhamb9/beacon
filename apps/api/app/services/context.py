from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.models.context import (
    BusinessContext,
    BusinessGoal,
    BusinessPain,
    CompanyProfile,
    ContextEvidence,
    ContextFeedback,
)
from app.repositories.context import ContextRepository
from context_engine import ContextPipeline


class ContextService:
    def __init__(self, repository: ContextRepository, pipeline: ContextPipeline | None = None) -> None:
        self.repository = repository
        self.pipeline = pipeline or ContextPipeline()

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        inputs = await self.repository.pending_context_inputs(limit=limit)
        for item in inputs:
            if await self.repository.has_context_for_signal(item.classified_signal_id):
                continue
            context, dna = self.pipeline.process(item)
            await self.repository.store_context(context, dna)
            processed += 1
        return {"processed": processed}

    async def company_context(self, company_id: UUID, *, limit: int) -> list[BusinessContext]:
        return list(await self.repository.latest_company_contexts(company_id, limit=limit))

    async def company_dna(self, company_id: UUID) -> CompanyProfile | None:
        return await self.repository.latest_company_profile(company_id)

    async def company_pains(self, company_id: UUID, *, limit: int) -> list[BusinessPain]:
        return list(await self.repository.company_pains(company_id, limit=limit))

    async def company_goals(self, company_id: UUID, *, limit: int) -> list[BusinessGoal]:
        return list(await self.repository.company_goals(company_id, limit=limit))

    async def company_timeline_context(self, company_id: UUID, *, limit: int) -> list[BusinessContext]:
        return list(await self.repository.latest_company_contexts(company_id, limit=limit))

    async def company_evidence(self, company_id: UUID, *, limit: int) -> list[ContextEvidence]:
        return list(await self.repository.company_evidence(company_id, limit=limit))

    async def statistics(self) -> dict[str, float | int | str]:
        since = datetime.now(UTC) - timedelta(days=1)
        stats = await self.repository.statistics(since=since)
        contexts = int(stats["contexts"])
        return {
            **stats,
            "window": "24h",
            "context_coverage": contexts,
            "rule_performance": contexts,
        }

    async def feedback(
        self,
        *,
        business_context_id: UUID,
        reviewer: str,
        review_outcome: str,
        corrected_fields: dict[str, object],
        ground_truth: dict[str, object],
        notes: str | None,
    ) -> ContextFeedback:
        return await self.repository.add_feedback(
            business_context_id=business_context_id,
            reviewer=reviewer,
            review_outcome=review_outcome,
            corrected_fields=corrected_fields,
            ground_truth=ground_truth,
            notes=notes,
        )
