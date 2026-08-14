"""Daily Revenue Report — morning brief for execution quality."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from revenue_execution_validation.models.types import (
    UNKNOWN,
    ConnectorScore,
    DailyRevenueReport,
    FounderQueueCardV3,
    RealityFunnel,
    RevSnapshot,
)


class DailyRevenueReportEngine:
    def build(
        self,
        *,
        snapshots: list[RevSnapshot],
        funnel: RealityFunnel,
        connectors: list[ConnectorScore],
        founder_queue: list[FounderQueueCardV3],
        rejection_top: list[dict[str, Any]] | None = None,
        prior_connector_pct: dict[str, float] | None = None,
    ) -> DailyRevenueReport:
        prior = prior_connector_pct or {}
        improved: list[str] = []
        declining: list[str] = []
        for c in connectors:
            prev = prior.get(c.connector)
            if prev is None:
                continue
            if c.revenue_ready_pct > prev + 2:
                improved.append(c.connector)
            elif c.revenue_ready_pct < prev - 2:
                declining.append(c.connector)

        top5 = [
            {
                "company": card.company,
                "website": card.website,
                "service": card.service_match,
                "email": card.verified_email,
                "why_now": card.why_now,
                "confidence": card.confidence,
            }
            for card in founder_queue[:5]
        ]
        biggest = UNKNOWN
        if rejection_top:
            biggest = str(rejection_top[0].get("reason") or UNKNOWN)

        ready = funnel.revenue_ready
        emails = sum(1 for s in snapshots if s.check.business_email)
        dms = sum(1 for s in snapshots if s.check.decision_maker)
        high_intent = sum(
            1
            for s in snapshots
            if s.check.intent_detected and s.check.confidence >= 70
        )

        if ready >= 25 and emails >= 15:
            rec = "Founder Queue is contactable — review Top 10 and approve outreach in sandbox."
        elif ready < 10:
            rec = "Focus connectors with Excellent/Good grades; disable Weak producers of platform-only noise."
        else:
            rec = "Increase verified business email recovery on Revenue Ready candidates before unlocking production."

        return DailyRevenueReport(
            signals_collected=funnel.total_signals,
            companies_verified=next((st.count for st in funnel.stages if st.name == "Verified Companies"), 0),
            revenue_ready=ready,
            decision_makers_found=dms,
            business_emails_found=emails,
            founder_queue=len(founder_queue),
            new_high_intent=high_intent,
            connectors_improved=improved,
            connectors_declining=declining,
            top_5_opportunities=top5,
            biggest_failure=biggest,
            recommendation=rec,
            generated_at=datetime.now(UTC).isoformat(),
            evidence=[f"ready:{ready}", f"emails:{emails}", f"dms:{dms}", f"fq:{len(founder_queue)}"],
        )
