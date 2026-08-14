"""Outcome tracker — records final outcomes for leads.

Append-only. Every outcome is immutable once recorded.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from validation_engine import DEAL_STATUSES
from validation_engine.models import DealEvent


class OutcomeTracker:
    """Tracks final outcomes (won/lost/paused) for companies."""

    def __init__(self) -> None:
        self._outcomes: dict[str, list[DealEvent]] = {}

    def record_outcome(
        self,
        company_id: str,
        status: str,
        *,
        revenue: float = 0.0,
        expected_revenue: float = 0.0,
        close_date: datetime | None = None,
        service_sold: str = "",
        reason: str = "",
        evidence: dict[str, Any] | None = None,
    ) -> DealEvent:
        if status not in DEAL_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {DEAL_STATUSES}")

        event = DealEvent(
            company_id=company_id,
            status=status,
            revenue=revenue,
            expected_revenue=expected_revenue,
            close_date=close_date,
            service_sold=service_sold,
            reason=reason,
            evidence=evidence or {},
        )
        self._outcomes.setdefault(company_id, []).append(event)
        return event

    def get_outcome(self, company_id: str) -> DealEvent | None:
        outcomes = self._outcomes.get(company_id, [])
        return outcomes[-1] if outcomes else None

    def get_all_outcomes(self) -> list[DealEvent]:
        result = []
        for outcomes in self._outcomes.values():
            result.extend(outcomes)
        return result

    def get_won_deals(self) -> list[DealEvent]:
        return [o for o in self.get_all_outcomes() if o.status == "won"]

    def get_lost_deals(self) -> list[DealEvent]:
        return [o for o in self.get_all_outcomes() if o.status == "lost"]

    def get_paused_deals(self) -> list[DealEvent]:
        return [o for o in self.get_all_outcomes() if o.status == "paused"]

    def get_total_revenue(self) -> float:
        return sum(d.revenue for d in self.get_won_deals())

    def get_win_rate(self) -> float:
        all_outcomes = self.get_all_outcomes()
        if not all_outcomes:
            return 0.0
        won = len([o for o in all_outcomes if o.status == "won"])
        return (won / len(all_outcomes)) * 100.0

    def get_avg_deal_size(self) -> float:
        won = self.get_won_deals()
        if not won:
            return 0.0
        return sum(d.revenue for d in won) / len(won)

    def get_outcomes_by_service(self) -> dict[str, list[DealEvent]]:
        result: dict[str, list[DealEvent]] = {}
        for outcome in self.get_all_outcomes():
            service = outcome.service_sold or "unknown"
            result.setdefault(service, []).append(outcome)
        return result

    def get_revenue_by_service(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for deal in self.get_won_deals():
            service = deal.service_sold or "unknown"
            result[service] = result.get(service, 0.0) + deal.revenue
        return result
