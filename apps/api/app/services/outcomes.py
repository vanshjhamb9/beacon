from __future__ import annotations

from uuid import UUID

from app.models.improvement import WeightAdjustment
from app.repositories.outcomes import OutcomeRepository
from outcome_intelligence.models.types import (
    CompanyOutcomeReport,
    OutcomeAnalytics,
    OutcomeDashboard,
    OutcomeUpdateInput,
)
from outcome_intelligence.services.outcomes import OutcomeIntelligenceService


class OutcomePlatformService:
    def __init__(
        self,
        repository: OutcomeRepository,
        intelligence: OutcomeIntelligenceService | None = None,
    ) -> None:
        self.repository = repository
        self.intelligence = intelligence or OutcomeIntelligenceService()

    async def update(self, payload: OutcomeUpdateInput) -> dict:
        result = await self.repository.update_outcome(payload)
        # Refresh accuracy + learning snapshots after each outcome write.
        await self._persist_learning_snapshot()
        return result

    async def dashboard(self) -> OutcomeDashboard:
        records = list(await self.repository.outcome_records())
        dashboard = self.intelligence.dashboard(records)
        await self.repository.persist_dashboard_metrics(dashboard)
        return dashboard

    async def analytics(self) -> OutcomeAnalytics:
        records = list(await self.repository.outcome_records())
        analytics = self.intelligence.analytics(records)
        return analytics

    async def company_report(self, company_id: UUID) -> CompanyOutcomeReport:
        payload = await self.repository.company_outcomes(company_id)
        return CompanyOutcomeReport(**payload)

    async def _persist_learning_snapshot(self) -> None:
        records = list(await self.repository.outcome_records(limit=5000))
        if not records:
            return
        dashboard = self.intelligence.dashboard(records)
        await self.repository.persist_dashboard_metrics(dashboard)
        await self._emit_improvement_recommendations(dashboard)

    async def _emit_improvement_recommendations(self, dashboard: OutcomeDashboard) -> None:
        """Feed Improvement Engine with approval-required recommendations only."""
        for recommendation in dashboard.learning_recommendations:
            self.repository.session.add(
                WeightAdjustment(
                    target_type=recommendation.area,
                    target_key=recommendation.target_key,
                    current_weight=None,
                    recommended_weight=None,
                    recommendation=recommendation.recommendation,
                    reason=recommendation.reason,
                    confidence=recommendation.confidence,
                    requires_approval="true",
                )
            )
        await self.repository.session.flush()
