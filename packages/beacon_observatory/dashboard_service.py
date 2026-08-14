"""Dashboard Service — observatory dashboard aggregation."""

from datetime import datetime, timezone
from typing import Any

from . import DEMO_KEYWORDS


class DashboardService:
    """Observatory dashboard aggregation service."""

    def __init__(self):
        self._metrics: dict[str, Any] = {}

    def get_trust_dashboard(
        self,
        runtime_stats: dict[str, Any],
        collector_stats: dict[str, Any],
        rejection_stats: dict[str, Any],
        latency_stats: dict[str, Any],
    ) -> dict[str, Any]:
        """Get trust dashboard data."""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "live_signals_today": runtime_stats.get("total_signals", 0),
            "signals_last_hour": runtime_stats.get("signals_last_hour", 0),
            "collectors_running": runtime_stats.get("running", 0),
            "collectors_failed": runtime_stats.get("failed", 0),
            "revenue_ready_today": runtime_stats.get("total_revenue_ready", 0),
            "rejected_today": rejection_stats.get("total_rejections", 0),
            "average_signal_age": runtime_stats.get("avg_signal_age", 0),
            "pipeline_delay": latency_stats.get("total_avg_ms", 0),
            "average_runtime": runtime_stats.get("avg_runtime", 0),
            "average_quality": runtime_stats.get("avg_quality", 0),
            "processing_latency": latency_stats.get("total_avg_ms", 0),
            "data_freshness": "live",
        }

    def detect_demo_data(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect demo or placeholder data."""
        demo_found = []

        for opp in opportunities:
            company_name = opp.get("company_name", "").lower()
            website = opp.get("website", "").lower()

            for keyword in DEMO_KEYWORDS:
                if keyword in company_name or keyword in website:
                    demo_found.append({
                        "opportunity_id": opp.get("id"),
                        "company_name": opp.get("company_name"),
                        "keyword_matched": keyword,
                        "severity": "critical",
                    })
                    break

        return demo_found

    def get_verification_summary(
        self,
        verification_stats: dict[str, Any],
    ) -> dict[str, Any]:
        """Get verification summary."""
        total = verification_stats.get("total_widgets", 0)
        live = verification_stats.get("live", 0)

        return {
            "total_widgets": total,
            "live_widgets": live,
            "verification_rate": round(live / max(total, 1), 3),
            "all_live": total == live,
        }
