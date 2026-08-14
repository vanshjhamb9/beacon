"""Deal tracker — records all deal events for companies.

Append-only. Never overwrites. Every deal outcome is immutable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import DEAL_STATUSES
from validation_engine.models import DealEvent


class DealTracker:
    """Tracks deal outcomes (won/lost/paused) with revenue attribution."""

    def __init__(self) -> None:
        self._deals: dict[str, list[DealEvent]] = {}
        self._all_deals: list[DealEvent] = []

    def record_deal(
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
            close_date=close_date or datetime.now(UTC),
            service_sold=service_sold,
            reason=reason,
            evidence=evidence or {},
        )
        self._deals.setdefault(company_id, []).append(event)
        self._all_deals.append(event)
        return event

    def get_deals_for_company(self, company_id: str) -> list[DealEvent]:
        return list(self._deals.get(company_id, []))

    def get_all_deals(self) -> list[DealEvent]:
        return list(self._all_deals)

    def get_won_deals(self) -> list[DealEvent]:
        return [d for d in self._all_deals if d.status == "won"]

    def get_lost_deals(self) -> list[DealEvent]:
        return [d for d in self._all_deals if d.status == "lost"]

    def get_paused_deals(self) -> list[DealEvent]:
        return [d for d in self._all_deals if d.status == "paused"]

    def get_total_revenue(self) -> float:
        return sum(d.revenue for d in self.get_won_deals())

    def get_total_expected_revenue(self) -> float:
        return sum(d.expected_revenue for d in self._all_deals if d.status != "lost")

    def get_win_rate(self) -> float:
        if not self._all_deals:
            return 0.0
        won = len(self.get_won_deals())
        return (won / len(self._all_deals)) * 100.0

    def get_avg_deal_size(self) -> float:
        won = self.get_won_deals()
        if not won:
            return 0.0
        return sum(d.revenue for d in won) / len(won)

    def get_avg_sales_cycle(self) -> float | None:
        cycles = []
        for deal in self._all_deals:
            if deal.close_date and deal.status in ("won", "lost"):
                cycles.append(deal.close_date)
        if len(cycles) < 2:
            return None
        return sum(
            (cycles[i + 1] - cycles[i]).total_seconds() / 86400.0
            for i in range(len(cycles) - 1)
        ) / (len(cycles) - 1)

    def get_revenue_by_service(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for deal in self.get_won_deals():
            service = deal.service_sold or "unknown"
            result[service] = result.get(service, 0.0) + deal.revenue
        return result

    def get_deals_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for deal in self._all_deals:
            counts[deal.status] = counts.get(deal.status, 0) + 1
        return counts

    def get_todays_deals(self) -> list[DealEvent]:
        today = datetime.now(UTC).date()
        return [d for d in self._all_deals if d.close_date and d.close_date.date() == today]
