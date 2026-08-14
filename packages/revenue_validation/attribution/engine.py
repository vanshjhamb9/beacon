"""Revenue attribution aggregates — from WON events only. Never invent revenue."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from revenue_validation.models.types import UNKNOWN, RevenueAttribution


class AttributionEngine:
    def build_won(
        self,
        *,
        company: str,
        company_id: str,
        brief: dict[str, Any],
        amount: float,
        currency: str = "USD",
        close_date: str | None,
        sales_cycle_days: float | None,
        proposal_value: float | None = None,
        source_connector: str | None = None,
        snapshot_id: str | None = None,
    ) -> RevenueAttribution:
        service = str(brief.get("recommended_service") or UNKNOWN)
        expected = float(proposal_value if proposal_value is not None else brief.get("pipeline_value") or amount)
        return RevenueAttribution(
            company=company,
            company_id=company_id,
            service_sold=service,
            revenue_amount=float(amount),
            currency=currency,
            close_date=close_date,
            sales_cycle_days=sales_cycle_days,
            proposal_value=float(proposal_value or expected),
            expected_revenue=expected,
            actual_revenue=float(amount),
            founder="Vansh",
            source_connector=str(source_connector or brief.get("source") or "yc"),
            revenue_ready_snapshot_id=snapshot_id,
        )

    def aggregates(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        total = sum(float(r.get("actual_revenue") or r.get("revenue_amount") or 0) for r in rows)
        by_connector: dict[str, float] = defaultdict(float)
        by_industry: dict[str, float] = defaultdict(float)
        by_service: dict[str, float] = defaultdict(float)
        by_role: dict[str, float] = defaultdict(float)
        for r in rows:
            amt = float(r.get("actual_revenue") or r.get("revenue_amount") or 0)
            by_connector[str(r.get("source_connector") or UNKNOWN)] += amt
            by_industry[str(r.get("industry") or UNKNOWN)] += amt
            by_service[str(r.get("service_sold") or UNKNOWN)] += amt
            by_role[str(r.get("decision_maker_role") or UNKNOWN)] += amt
        return {
            "total_revenue": round(total, 2),
            "monthly_revenue": round(total, 2),  # single-period until history grows
            "quarterly_revenue": round(total, 2),
            "revenue_per_connector": dict(by_connector),
            "revenue_per_industry": dict(by_industry),
            "revenue_per_service": dict(by_service),
            "revenue_per_decision_maker_role": dict(by_role),
            "deal_count": len(rows),
            "average_deal_size": round(total / len(rows), 2) if rows else 0.0,
            "largest_deal": max((float(r.get("actual_revenue") or 0) for r in rows), default=0.0),
        }
