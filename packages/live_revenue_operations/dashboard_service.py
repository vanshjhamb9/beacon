"""Dashboard Service — aggregates all metrics for the dashboard."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DashboardService:
    """Aggregates all metrics for the revenue operations dashboard."""

    def __init__(self):
        self._metrics: dict[str, Any] = {}

    def get_top_cards(self) -> dict[str, Any]:
        """Get top dashboard cards."""
        return {
            "signals_today": self._metrics.get("signals_today", 0),
            "signals_this_hour": self._metrics.get("signals_this_hour", 0),
            "accepted_today": self._metrics.get("accepted_today", 0),
            "rejected_today": self._metrics.get("rejected_today", 0),
            "revenue_ready_today": self._metrics.get("revenue_ready_today", 0),
            "contacted_today": self._metrics.get("contacted_today", 0),
            "replies_today": self._metrics.get("replies_today", 0),
            "meetings_today": self._metrics.get("meetings_today", 0),
            "pipeline_value": self._metrics.get("pipeline_value", 0.0),
            "connector_health": self._metrics.get("connector_health", "unknown"),
            "avg_signal_age": self._metrics.get("avg_signal_age", 0),
            "avg_quality": self._metrics.get("avg_quality", 0),
            "acceptance_rate": self._metrics.get("acceptance_rate", 0.0),
        }

    def update_metrics(self, metrics: dict[str, Any]):
        """Update dashboard metrics."""
        self._metrics.update(metrics)

    def get_full_dashboard(
        self,
        inbox_stats: dict[str, Any] | None = None,
        pipeline_stats: dict[str, Any] | None = None,
        outreach_stats: dict[str, Any] | None = None,
        reply_stats: dict[str, Any] | None = None,
        meeting_stats: dict[str, Any] | None = None,
        proposal_stats: dict[str, Any] | None = None,
        revenue_stats: dict[str, Any] | None = None,
        connector_stats: dict[str, Any] | None = None,
        aging_stats: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get full dashboard data."""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "top_cards": self.get_top_cards(),
            "inbox": inbox_stats or {},
            "pipeline": pipeline_stats or {},
            "outreach": outreach_stats or {},
            "replies": reply_stats or {},
            "meetings": meeting_stats or {},
            "proposals": proposal_stats or {},
            "revenue": revenue_stats or {},
            "connectors": connector_stats or {},
            "aging": aging_stats or {},
        }
