from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.repositories.revenue_hunter import RevenueHunterRepository
from revenue_hunter import RevenueHunterPipeline, RevenueHunterService
from revenue_hunter.filters.taxonomy import (
    COMPANY_SIZE_BANDS,
    FUNDING_STAGES,
    REVENUE_BANDS,
    TARGET_COUNTRIES,
    TARGET_INDUSTRIES,
    default_filter_criteria,
)
from revenue_hunter.models.types import BeaconService


class RevenueHunterPlatformService:
    def __init__(self, repository: RevenueHunterRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        self._engine: RevenueHunterService | None = None

    def _service(self) -> RevenueHunterService:
        if self._engine is None:
            criteria = default_filter_criteria()
            pipeline = RevenueHunterPipeline(
                criteria=criteria,
                a_plus_threshold=self.settings.revenue_hunter_a_plus_threshold,
                a_threshold=self.settings.revenue_hunter_a_threshold,
            )
            self._engine = RevenueHunterService(criteria=criteria, pipeline=pipeline)
        return self._engine

    async def process_pending(self, *, limit: int) -> dict[str, int]:
        engine = self._service()
        processed = 0
        campaign = 0
        a_plus = 0
        for item in await self.repository.pending_inputs(limit=limit):
            decision = engine.evaluate(item)
            await self.repository.store_decision(decision)
            processed += 1
            if decision.proceed_to_campaign:
                campaign += 1
            if decision.priority_grade.value == "A+":
                a_plus += 1
        return {"processed": processed, "campaign_eligible": campaign, "a_plus": a_plus}

    async def list_dossiers(
        self, *, grade: str | None, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        rows = await self.repository.list_dossiers(grade=grade, limit=limit, offset=offset)
        return [self._dossier_dict(row) for row in rows]

    async def get_dossier(self, dossier_id: UUID) -> dict[str, Any] | None:
        row = await self.repository.get_dossier(dossier_id)
        if row is None:
            return None
        return self._dossier_dict(row)

    async def work_queue(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        rows = await self.repository.list_work_queue(status=status, limit=limit)
        return [self._queue_dict(row) for row in rows]

    async def apply_action(self, item_id: UUID, *, action: str, actor: str) -> dict[str, Any] | None:
        row = await self.repository.apply_work_action(item_id, action=action, actor=actor)
        if row is None:
            return None
        return self._queue_dict(row)

    async def founder_dashboard(self) -> dict[str, Any]:
        rows = await self.repository.list_dossiers(limit=200, offset=0)
        dossiers = await self.repository.dossiers_as_domain(rows)
        queue_pending = await self.repository.list_work_queue(status="pending", limit=500)
        replied = await self.repository.list_work_queue(status="replied", limit=500)
        meetings = await self.repository.list_work_queue(status="meeting_booked", limit=500)
        dashboard = self._service().build_dashboard(
            dossiers,
            meetings_today=len(meetings),
            campaign_queue=sum(1 for r in rows if r.proceed_to_campaign),
            reply_queue=len(replied),
            follow_ups=len(queue_pending),
        )
        await self.repository.store_daily_brief(dashboard)
        return {
            "todays_targets": [t.model_dump(mode="json") for t in dashboard.todays_targets],
            "top_25_companies": dashboard.top_25_companies,
            "expected_revenue": dashboard.expected_revenue,
            "expected_pipeline": dashboard.expected_pipeline,
            "meetings_today": dashboard.meetings_today,
            "campaign_queue": dashboard.campaign_queue,
            "reply_queue": dashboard.reply_queue,
            "follow_ups": dashboard.follow_ups,
            "hot_opportunities": dashboard.hot_opportunities,
            "generated_at": dashboard.generated_at.isoformat() if dashboard.generated_at else None,
        }

    def taxonomy(self) -> dict[str, list[str]]:
        return {
            "countries": list(TARGET_COUNTRIES),
            "company_sizes": list(COMPANY_SIZE_BANDS),
            "industries": list(TARGET_INDUSTRIES),
            "funding_stages": list(FUNDING_STAGES),
            "revenue_bands": list(REVENUE_BANDS),
            "services": [s.value for s in BeaconService],
        }

    def _dossier_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": row.id,
            "company_id": row.company_id,
            "opportunity_id": row.opportunity_id,
            "company_name": row.company_name,
            "industry": row.industry,
            "country": row.country,
            "company_size_band": row.company_size_band,
            "funding_stage": row.funding_stage,
            "revenue_band": row.revenue_band,
            "filter_passed": row.filter_passed,
            "filter_match": row.filter_match,
            "recommended_service": row.recommended_service,
            "service_confidence": row.service_confidence,
            "service_matches": row.service_matches,
            "pain_points": row.pain_points,
            "website_intelligence": row.website_intelligence,
            "why_now": row.why_now,
            "dossier": row.dossier,
            "priority_grade": row.priority_grade,
            "revenue_score": row.revenue_score,
            "expected_budget": row.expected_budget,
            "expected_timeline": row.expected_timeline,
            "probability": row.probability,
            "proceed_to_campaign": row.proceed_to_campaign,
            "work_queue_eligible": row.work_queue_eligible,
            "score_breakdown": row.score_breakdown,
            "evidence_chain": row.evidence_chain,
            "explanations": row.explanations,
            "scoring_version": row.scoring_version,
            "created_at": row.created_at,
        }

    def _queue_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": row.id,
            "dossier_id": row.dossier_id,
            "company_id": row.company_id,
            "company_name": row.company_name,
            "priority_grade": row.priority_grade,
            "recommended_service": row.recommended_service,
            "why_today": row.why_today,
            "expected_budget": row.expected_budget,
            "probability": row.probability,
            "primary_contact": row.primary_contact,
            "status": row.status,
            "allowed_actions": row.allowed_actions,
            "rank": row.rank,
            "action_log": row.action_log,
            "acted_at": row.acted_at,
            "created_at": row.created_at,
        }
