"""Daily and weekly quality reports."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import QualityDecision, QualitySnapshot


class QualityReportGenerator:
    def __init__(self, dashboard: QualityDashboard) -> None:
        self._dashboard = dashboard

    def daily_report(self, *, date: datetime | None = None) -> dict[str, Any]:
        target = date or datetime.now(UTC)
        snap = self._dashboard.snapshot(now=target)

        return {
            "report_type": "daily",
            "date": target.date().isoformat(),
            "collected": snap.signals_collected,
            "accepted": snap.signals_accepted,
            "rejected": snap.signals_rejected,
            "acceptance_pct": round(snap.acceptance_rate, 2),
            "top_connector": self._top_connector(snap),
            "worst_connector": self._worst_connector(snap),
            "top_rejection_reason": self._top_rejection_reason(snap),
            "freshest_opportunities": self._freshest(),
            "oldest_rejected": self._oldest_rejected(),
            "freshness_failures": snap.freshness_failures,
            "duplicate_failures": snap.duplicate_failures,
            "competitor_failures": snap.competitor_failures,
            "website_failures": snap.website_failures,
            "buying_signal_failures": snap.buying_signal_failures,
            "ai_company_failures": snap.ai_company_failures,
            "icp_failures": snap.icp_failures,
            "region_failures": snap.region_failures,
            "source_trust_failures": snap.source_trust_failures,
            "activity_failures": snap.activity_failures,
            "expired_opportunities": snap.expired_opportunities,
            "connector_quality": snap.connector_quality,
            "top_rejection_reasons": snap.top_rejection_reasons,
        }

    def weekly_report(self, *, week_ending: datetime | None = None) -> dict[str, Any]:
        target = week_ending or datetime.now(UTC)
        snap = self._dashboard.snapshot(now=target)

        return {
            "report_type": "weekly",
            "week_ending": target.date().isoformat(),
            "total_collected": snap.signals_collected,
            "total_accepted": snap.signals_accepted,
            "total_rejected": snap.signals_rejected,
            "acceptance_pct": round(snap.acceptance_rate, 2),
            "freshness_failures": snap.freshness_failures,
            "duplicate_failures": snap.duplicate_failures,
            "competitor_failures": snap.competitor_failures,
            "website_failures": snap.website_failures,
            "buying_signal_failures": snap.buying_signal_failures,
            "ai_company_failures": snap.ai_company_failures,
            "icp_failures": snap.icp_failures,
            "region_failures": snap.region_failures,
            "source_trust_failures": snap.source_trust_failures,
            "activity_failures": snap.activity_failures,
            "expired_opportunities": snap.expired_opportunities,
            "connector_quality": snap.connector_quality,
            "top_rejection_reasons": snap.top_rejection_reasons,
        }

    def _top_connector(self, snap: QualitySnapshot) -> str:
        if not snap.connector_quality:
            return "N/A"
        return max(snap.connector_quality, key=snap.connector_quality.get)  # type: ignore[arg-type]

    def _worst_connector(self, snap: QualitySnapshot) -> str:
        if not snap.connector_quality:
            return "N/A"
        return min(snap.connector_quality, key=snap.connector_quality.get)  # type: ignore[arg-type]

    def _top_rejection_reason(self, snap: QualitySnapshot) -> str:
        if not snap.top_rejection_reasons:
            return "N/A"
        return snap.top_rejection_reasons[0].get("reason", "N/A")

    def _freshest(self) -> list[dict[str, Any]]:
        events = self._dashboard.events_by_decision(QualityDecision.ACCEPT)
        return [
            {"company": e.company_name, "signal": e.signal_type}
            for e in events[:5]
        ]

    def _oldest_rejected(self) -> list[dict[str, Any]]:
        events = self._dashboard.events_by_decision(QualityDecision.REJECT)
        return [
            {"company": e.company_name, "signal": e.signal_type, "reasons": e.rejection_reasons}
            for e in events[-5:]
        ]
