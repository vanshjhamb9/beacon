from typing import Any
from uuid import UUID

from app.repositories.enrichment import EnrichmentRepository
from app.repositories.verification import VerificationRepository
from app.services.enrichment import LeadEnrichmentService
from data_verification import VerificationPipeline
from data_verification.models.types import AutomaticAction, ConnectorStatistic, DashboardMetrics


class DataVerificationService:
    def __init__(
        self,
        repository: VerificationRepository,
        pipeline: VerificationPipeline | None = None,
        enrichment_service: LeadEnrichmentService | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or VerificationPipeline()
        self.enrichment_service = enrichment_service

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        processed = 0
        refresh_queued = 0
        flagged = 0
        scheduled_refresh = 0
        inputs = await self.repository.pending_verification_inputs(limit=limit)
        for item in inputs:
            result = self.pipeline.process(item)
            await self.repository.store_verification(result)
            processed += 1
            if AutomaticAction.FLAG_FOR_REVIEW in result.automatic_actions:
                flagged += 1
            if AutomaticAction.SCHEDULE_ENRICHMENT_REFRESH in result.automatic_actions:
                scheduled_refresh += 1
            # Auto-queue re-enrichment only when freshness expired (avoids completeness refresh loops).
            if (
                self.enrichment_service is not None
                and AutomaticAction.QUEUE_REENRICHMENT in result.automatic_actions
            ):
                await self.enrichment_service.refresh(result.company_id)
                refresh_queued += 1
        return {
            "processed": processed,
            "refresh_queued": refresh_queued,
            "flagged_for_review": flagged,
            "scheduled_refresh": scheduled_refresh,
        }

    async def company_verification(self, company_id: UUID) -> dict[str, Any] | None:
        return await self.repository.company_payload(company_id)

    async def profile_verification(self, verification_report_id: UUID) -> dict[str, Any] | None:
        return await self.repository.profile_payload(verification_report_id)

    async def dashboard(self) -> DashboardMetrics:
        return await self.repository.dashboard_metrics()

    async def connectors(self) -> list[ConnectorStatistic]:
        return await self.repository.connector_leaderboard()

    async def refresh(self, entity_id: UUID) -> dict[str, Any] | None:
        enrichment_repo = EnrichmentRepository(self.repository.session)
        report = await enrichment_repo.latest_report_for_company(entity_id)
        enrichment_report_id = report.id if report is not None else entity_id
        item = await self.repository.verification_input(enrichment_report_id, force_refresh=True)
        if item is None:
            verification = await self.repository.latest_report_by_id(entity_id)
            if verification is None:
                company_report = await self.repository.latest_report_for_company(entity_id)
                if company_report is None:
                    return None
                item = await self.repository.verification_input(
                    company_report.enrichment_report_id,
                    force_refresh=True,
                )
            else:
                item = await self.repository.verification_input(
                    verification.enrichment_report_id,
                    force_refresh=True,
                )
        if item is None:
            return None
        result = self.pipeline.process(item)
        await self.repository.store_verification(result)
        return await self.repository.company_payload(result.company_id)
