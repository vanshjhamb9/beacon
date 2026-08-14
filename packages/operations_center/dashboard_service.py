"""Assemble the live Operations Center dashboard payload."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from operations_center import SCORING_VERSION
from operations_center.collector_monitor import top_failure_reasons
from operations_center.connector_monitor import ensure_known_connectors
from operations_center.health_engine import evaluate_health
from operations_center.metrics_engine import revenue_engine, today_progress, top_row_cards
from operations_center.models import (
    FailureView,
    FeedEvent,
    LiveDashboard,
    SourceMapNode,
    StageMetric,
)
from operations_center.pipeline_monitor import build_stage_metrics, conversion_chain
from operations_center.queue_monitor import build_queue_views
from operations_center.worker_monitor import build_worker_views


class DashboardService:
    """Pure assembler — callers supply already-queried counts and health rows."""

    def build(
        self,
        *,
        current: dict[str, int],
        today: dict[str, int],
        yesterday: dict[str, int],
        hour: dict[str, int],
        trends: dict[str, list[int]] | None = None,
        connectors: list[Any] | None = None,
        workers_inspect: dict[str, Any] | None = None,
        worker_stats: dict[str, dict[str, Any]] | None = None,
        queue_sizes: dict[str, int] | None = None,
        failures: list[tuple[str, int]] | None = None,
        feed: list[FeedEvent] | None = None,
        timeline: list[Any] | None = None,
        started_revenue_ready: int = 0,
        pipeline_value: float = 0.0,
        meetings: int = 0,
        won: int = 0,
        source_map: list[SourceMapNode] | None = None,
        ingestion_events: list[dict[str, Any]] | None = None,
    ) -> LiveDashboard:
        stages = build_stage_metrics(
            current=current,
            today=today,
            yesterday=yesterday,
            hour=hour,
            trends=trends,
        )
        conversions = conversion_chain(stages)
        connector_rows = ensure_known_connectors(list(connectors or []))
        workers = build_worker_views(
            inspect_payload=workers_inspect,
            queue_sizes=queue_sizes,
            stats=worker_stats,
        )
        queues = build_queue_views(queue_sizes)

        failure_rows: list[FailureView]
        if failures is not None:
            failure_rows = [FailureView(reason=r, count=c) for r, c in failures]
        else:
            failure_rows = [
                FailureView(reason=r, count=c)
                for r, c in top_failure_reasons(ingestion_events or [], limit=10)
            ]

        progress = today_progress(
            started=started_revenue_ready,
            current=int(current.get("revenue_ready", 0) or 0),
        )
        revenue = revenue_engine(
            pipeline_value=pipeline_value,
            meetings=meetings or int(current.get("meetings", 0) or 0),
            won=won or int(current.get("won", 0) or 0),
        )
        health = evaluate_health(
            signals_today=int(today.get("signals", 0) or 0),
            connectors=connector_rows,
            workers=workers,
            conversions=conversions,
        )
        cards = top_row_cards(stages, pipeline_value=revenue.pipeline, meetings=revenue.meetings)

        return LiveDashboard(
            generated_at=datetime.now(UTC),
            cards=cards,
            pipeline=stages,
            conversions=conversions,
            connectors=connector_rows,
            workers=workers,
            queues=queues,
            failures=failure_rows,
            feed=list(feed or []),
            timeline=list(timeline or []),
            progress=progress,
            revenue=revenue,
            source_map=list(source_map or []),
            health=health,
            scoring_version=SCORING_VERSION,
        )

    def to_dict(self, dashboard: LiveDashboard) -> dict[str, Any]:
        payload = asdict(dashboard)
        payload["generated_at"] = dashboard.generated_at.isoformat()
        for row in payload.get("connectors", []):
            for key in ("last_run", "last_success", "last_failure"):
                if row.get(key) is not None:
                    row[key] = row[key].isoformat() if hasattr(row[key], "isoformat") else row[key]
        for row in payload.get("workers", []):
            if row.get("last_execution") is not None and hasattr(row["last_execution"], "isoformat"):
                row["last_execution"] = row["last_execution"].isoformat()
        for row in payload.get("feed", []):
            if row.get("timestamp") is not None and hasattr(row["timestamp"], "isoformat"):
                row["timestamp"] = row["timestamp"].isoformat()
        return payload

    def stage_label(self, stage: str) -> str:
        labels = {
            "signals": "Signals",
            "identity_candidates": "Identity Candidates",
            "verified_websites": "Verified Websites",
            "companies": "Companies",
            "emails": "Emails",
            "decision_makers": "Decision Makers",
            "sales_ready": "Sales Ready",
            "revenue_ready": "Revenue Ready",
            "contacted": "Contacted",
            "meetings": "Meetings",
            "won": "Won",
        }
        return labels.get(stage, stage.replace("_", " ").title())

    def serialize_pipeline(self, stages: list[StageMetric]) -> list[dict[str, Any]]:
        return [
            {
                "stage": s.stage,
                "label": self.stage_label(s.stage),
                "current": s.current,
                "today": s.today,
                "yesterday": s.yesterday,
                "hour": s.hour,
                "trend_7d": s.trend_7d,
                "delta_pct": s.delta_pct,
            }
            for s in stages
        ]
