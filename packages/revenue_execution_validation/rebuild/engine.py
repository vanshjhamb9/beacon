"""Rebuild report — funnel + scoreboard + gates + daily."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from revenue_execution_validation.acceptance.engine import AcceptanceGateEngine
from revenue_execution_validation.connector_scoreboard.engine import ConnectorScoreboardEngine
from revenue_execution_validation.daily_report.engine import DailyRevenueReportEngine
from revenue_execution_validation.founder_queue_v3.engine import FounderQueueV3Engine
from revenue_execution_validation.funnel.engine import RealityFunnelEngine
from revenue_execution_validation.models.types import RevRebuildReport, RevSnapshot
from revenue_execution_validation.rejection.engine import RejectionAnalysisEngine


class RevRebuildEngine:
    def __init__(self) -> None:
        self.funnel = RealityFunnelEngine()
        self.rejection = RejectionAnalysisEngine()
        self.connectors = ConnectorScoreboardEngine()
        self.queue = FounderQueueV3Engine()
        self.acceptance = AcceptanceGateEngine()
        self.daily = DailyRevenueReportEngine()

    def build(
        self,
        snapshots: list[RevSnapshot],
        *,
        signals_collected: int | None = None,
        qa_accuracy: float = 0.0,
        qa_sample_size: int = 0,
        prior_connector_pct: dict[str, float] | None = None,
        outreach_counts: dict[str, int] | None = None,
    ) -> RevRebuildReport:
        t0 = perf_counter()
        outreach = outreach_counts or {}
        cards = self.queue.build(snapshots)
        funnel = self.funnel.build(
            snapshots,
            signals_collected=signals_collected,
            approved=int(outreach.get("approved") or 0),
            sent=int(outreach.get("sent") or 0),
            replies=int(outreach.get("replies") or 0),
            meetings=int(outreach.get("meetings") or 0),
            won=int(outreach.get("won") or 0),
            founder_queue_ids={c.company_id for c in cards},
        )
        rej = self.rejection.analyze(snapshots)
        scores = self.connectors.score(snapshots)
        gate = self.acceptance.evaluate(
            snapshots,
            founder_queue=cards,
            qa_accuracy=qa_accuracy,
            qa_sample_size=qa_sample_size,
        )
        daily = self.daily.build(
            snapshots=snapshots,
            funnel=funnel,
            connectors=scores,
            founder_queue=cards,
            rejection_top=rej.get("top_rejection_reasons"),
            prior_connector_pct=prior_connector_pct,
        )
        return RevRebuildReport(
            total_evaluated=len(snapshots),
            revenue_ready=funnel.revenue_ready,
            founder_queue=len(cards),
            funnel=funnel,
            connector_scores=scores,
            rejection_top=list(rej.get("top_rejection_reasons") or []),
            acceptance=gate,
            daily=daily,
            elapsed_ms=round((perf_counter() - t0) * 1000, 2),
            evidence=[
                f"evaluated:{len(snapshots)}",
                f"ready:{funnel.revenue_ready}",
                f"unlocked:{gate.production_unlocked}",
            ],
        )
