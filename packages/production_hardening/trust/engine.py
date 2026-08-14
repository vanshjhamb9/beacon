from __future__ import annotations

from typing import Any

from production_hardening.models.types import TrustMetrics


class TrustMetricsEngine:
    """QA / trust dashboard metrics from counted pipeline facts."""

    def evaluate(self, stats: dict[str, Any]) -> TrustMetrics:
        collected = int(stats.get("companies_collected") or 0)
        qualified = int(stats.get("qualified") or 0)
        rejected = int(stats.get("rejected") or 0)
        merged = int(stats.get("merged") or 0)
        with_website = int(stats.get("with_website") or 0)
        with_email = int(stats.get("with_email") or 0)
        with_phone = int(stats.get("with_phone") or 0)
        with_dm = int(stats.get("with_decision_maker") or 0)
        denom = max(collected, 1)

        return TrustMetrics(
            companies_collected=collected,
            qualified=qualified,
            rejected=rejected,
            merged=merged,
            duplicate_percent=round(float(stats.get("duplicate_percent") or (merged / denom * 100.0)), 2),
            verified_websites_percent=round(with_website / denom * 100.0, 2),
            verified_emails_percent=round(with_email / denom * 100.0, 2),
            verified_phones_percent=round(with_phone / denom * 100.0, 2),
            decision_makers_percent=round(with_dm / denom * 100.0, 2),
            average_confidence=round(float(stats.get("average_confidence") or 0.0), 2),
            average_freshness_hours=(
                float(stats["average_freshness_hours"])
                if stats.get("average_freshness_hours") is not None
                else None
            ),
            collector_health=dict(stats.get("collector_health") or {}),
            daily_pipeline_conversion=dict(stats.get("daily_pipeline_conversion") or {}),
            evidence=[
                f"collected:{collected}",
                f"qualified:{qualified}",
                f"rejected:{rejected}",
                f"merged:{merged}",
            ],
        )
