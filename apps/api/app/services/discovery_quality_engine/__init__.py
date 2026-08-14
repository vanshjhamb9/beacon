"""Discovery Quality Engine service layer for API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from discovery_quality_engine.activity_engine import ActivityEngine, ActivityEvidence
from discovery_quality_engine.buying_signal_engine import BuyingSignalEngine
from discovery_quality_engine.company_age import CompanyAgeFilter
from discovery_quality_engine.company_filter import CompanyFilter
from discovery_quality_engine.competitor_engine import CompetitorConfig, CompetitorEngine
from discovery_quality_engine.duplicate_engine import DuplicateEngine
from discovery_quality_engine.freshness_engine import FreshnessEngine
from discovery_quality_engine.industry_filter import IndustryFilter
from discovery_quality_engine.quality_dashboard import QualityDashboard
from discovery_quality_engine.quality_engine import QualityDecision, QualityEvent
from discovery_quality_engine.quality_metrics import QualityMetricsCollector
from discovery_quality_engine.quality_reports import QualityReportGenerator
from discovery_quality_engine.region_filter import RegionFilter
from discovery_quality_engine.signal_filter import SignalFilter
from discovery_quality_engine.source_quality import SourceQualityEngine
from discovery_quality_engine.technology_filter import TechnologyFilter
from discovery_quality_engine.website_quality import WebsiteQualityEngine
from discovery_quality_engine.dqe_orchestrator import DQEOrchestrator


class DiscoveryQualityService:
    def __init__(
        self,
        *,
        competitor_config: CompetitorConfig | None = None,
    ) -> None:
        self._dashboard = QualityDashboard()
        self._metrics = QualityMetricsCollector()
        self._orchestrator = DQEOrchestrator(
            dashboard=self._dashboard,
            metrics=self._metrics,
            competitor_engine=CompetitorEngine(config=competitor_config),
        )
        self._report_gen = QualityReportGenerator(self._dashboard)

    async def dashboard(self) -> dict[str, Any]:
        return self._dashboard.summary()

    async def rejections(
        self,
        reason: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        events = self._dashboard.events_by_decision(QualityDecision.REJECT)
        if reason:
            events = [e for e in events if reason in e.rejection_reasons]
        events = events[:limit]
        return {
            "items": [
                {
                    "company_name": e.company_name,
                    "signal_type": e.signal_type,
                    "source": e.source,
                    "rejection_reasons": e.rejection_reasons,
                    "gates_failed": e.gates_failed,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ],
            "count": len(events),
        }

    async def connector_quality(self) -> dict[str, Any]:
        metrics = self._metrics.build()
        return {
            "connectors": [
                {
                    "name": cm.connector_name,
                    "total_signals": cm.total_signals,
                    "accepted": cm.accepted,
                    "rejected": cm.rejected,
                    "acceptance_rate": round(cm.acceptance_rate, 2),
                    "avg_trust_score": round(cm.avg_trust_score, 2),
                }
                for cm in metrics.connector_metrics.values()
            ]
        }

    async def company_quality(self, limit: int = 100) -> dict[str, Any]:
        events = self._dashboard.events_by_decision(QualityDecision.ACCEPT)
        company_stats: dict[str, dict[str, Any]] = {}
        for e in events:
            if e.company_name not in company_stats:
                company_stats[e.company_name] = {
                    "company_name": e.company_name,
                    "accepted": 0,
                    "rejected": 0,
                }
            company_stats[e.company_name]["accepted"] += 1

        rejected = self._dashboard.events_by_decision(QualityDecision.REJECT)
        for e in rejected:
            if e.company_name not in company_stats:
                company_stats[e.company_name] = {
                    "company_name": e.company_name,
                    "accepted": 0,
                    "rejected": 0,
                }
            company_stats[e.company_name]["rejected"] += 1

        items = sorted(company_stats.values(), key=lambda x: -x["accepted"])[:limit]
        return {"items": items, "count": len(items)}

    async def signal_quality(self) -> dict[str, Any]:
        metrics = self._metrics.build()
        return {
            "signals": [
                {
                    "gate": gm.gate_name,
                    "total_evaluated": gm.total_evaluated,
                    "passed": gm.total_passed,
                    "failed": gm.total_failed,
                    "avg_duration_ms": round(gm.avg_duration_ms, 2),
                }
                for gm in metrics.gate_metrics.values()
            ]
        }

    async def daily_report(self) -> dict[str, Any]:
        return self._report_gen.daily_report()

    async def weekly_report(self) -> dict[str, Any]:
        return self._report_gen.weekly_report()

    async def failures(
        self,
        gate: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        events = self._dashboard.events_by_decision(QualityDecision.REJECT)
        if gate:
            events = [e for e in events if gate in e.gates_failed]
        events = events[:limit]
        return {
            "items": [
                {
                    "company_name": e.company_name,
                    "signal_type": e.signal_type,
                    "gate": gate,
                    "rejection_reasons": e.rejection_reasons,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
                for gate in e.gates_failed
            ],
            "count": len(events),
        }

    async def freshness_stats(self) -> dict[str, Any]:
        events = self._dashboard.events_by_decision(QualityDecision.REJECT)
        freshness_events = [
            e for e in events if "STALE_SIGNAL" in e.rejection_reasons
        ]
        return {
            "total_stale": len(freshness_events),
            "items": [
                {
                    "company_name": e.company_name,
                    "signal_type": e.signal_type,
                    "rejection_reasons": e.rejection_reasons,
                    "created_at": e.created_at.isoformat(),
                }
                for e in freshness_events[:100]
            ],
        }
