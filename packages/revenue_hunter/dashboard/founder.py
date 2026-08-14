from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from revenue_hunter.models.types import FounderDashboard, PriorityGrade, RevenueDossier, WorkQueueItem
from revenue_hunter.queue.work_queue import WorkQueueBuilder


class FounderDashboardBuilder:
    """Morning briefing: who to contact, pipeline, queues, hot opportunities."""

    def __init__(self, queue_builder: WorkQueueBuilder | None = None) -> None:
        self.queue_builder = queue_builder or WorkQueueBuilder()

    def build(
        self,
        dossiers: list[RevenueDossier],
        *,
        meetings_today: int = 0,
        campaign_queue: int = 0,
        reply_queue: int = 0,
        follow_ups: int = 0,
    ) -> FounderDashboard:
        ranked = sorted(dossiers, key=lambda d: (-d.revenue_score, d.company_name))
        todays = self.queue_builder.build(ranked, limit=25)
        top_25 = [self._company_row(d) for d in ranked[:25]]
        hot = sum(1 for d in ranked if d.priority_grade in {PriorityGrade.A_PLUS, PriorityGrade.A})
        expected_revenue = sum(self._mid_budget(d) * (d.probability / 100.0) for d in ranked if d.proceed_to_campaign)
        expected_pipeline = sum(self._mid_budget(d) for d in ranked if d.proceed_to_campaign)

        return FounderDashboard(
            todays_targets=todays,
            top_25_companies=top_25,
            expected_revenue=round(expected_revenue, 2),
            expected_pipeline=round(expected_pipeline, 2),
            meetings_today=meetings_today,
            campaign_queue=campaign_queue if campaign_queue else sum(1 for d in ranked if d.proceed_to_campaign),
            reply_queue=reply_queue,
            follow_ups=follow_ups,
            hot_opportunities=hot,
            generated_at=datetime.now(UTC),
        )

    def _company_row(self, d: RevenueDossier) -> dict[str, Any]:
        return {
            "company_id": str(d.company_id),
            "company_name": d.company_name,
            "priority_grade": d.priority_grade.value,
            "revenue_score": d.revenue_score,
            "recommended_service": d.recommended_service,
            "expected_budget": d.expected_budget,
            "probability": d.probability,
            "proceed_to_campaign": d.proceed_to_campaign,
        }

    def _mid_budget(self, d: RevenueDossier) -> float:
        """Parse midpoint from ranges like '$25k–$55k'."""
        text = d.expected_budget.replace("$", "").replace(",", "").lower()
        parts = text.replace("–", "-").split("-")
        nums: list[float] = []
        for part in parts:
            part = part.strip()
            mult = 1.0
            if part.endswith("k"):
                mult = 1_000.0
                part = part[:-1]
            elif part.endswith("m"):
                mult = 1_000_000.0
                part = part[:-1]
            try:
                nums.append(float(part) * mult)
            except ValueError:
                continue
        if not nums:
            return 40_000.0
        return sum(nums) / len(nums)
