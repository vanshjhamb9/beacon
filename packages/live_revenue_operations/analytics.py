"""Analytics — analyzes revenue operations data for insights."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class Analytics:
    """Analyzes revenue operations data."""

    def __init__(self):
        self._data: dict[str, Any] = {}

    def analyze_pipeline(
        self,
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze pipeline health and trends."""
        total = len(opportunities)
        if total == 0:
            return {"total": 0, "health": "empty"}

        by_stage = {}
        for opp in opportunities:
            stage = opp.get("stage", "unknown")
            by_stage[stage] = by_stage.get(stage, 0) + 1

        # Calculate velocity
        avg_age = 0
        ages = []
        for opp in opportunities:
            created = opp.get("created_at")
            if created:
                try:
                    if isinstance(created, str):
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    else:
                        dt = created
                    age = (datetime.now(timezone.utc) - dt).days
                    ages.append(age)
                except (ValueError, AttributeError):
                    pass

        if ages:
            avg_age = sum(ages) / len(ages)

        # Health score
        active_stages = ["contacted", "replied", "meeting", "proposal", "negotiation"]
        active_count = sum(by_stage.get(s, 0) for s in active_stages)
        won_count = by_stage.get("won", 0)
        health_score = ((active_count / total) * 50 + (won_count / total) * 50) if total > 0 else 0

        return {
            "total": total,
            "by_stage": by_stage,
            "avg_age_days": round(avg_age, 2),
            "health_score": round(health_score, 2),
            "health_status": "healthy" if health_score >= 70 else "warning" if health_score >= 40 else "critical",
        }

    def analyze_connectors(
        self,
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze connector performance."""
        connector_stats: dict[str, dict[str, Any]] = {}

        for opp in opportunities:
            connector = opp.get("connector", "unknown")
            if connector not in connector_stats:
                connector_stats[connector] = {"total": 0, "revenue_ready": 0, "contacted": 0}
            connector_stats[connector]["total"] += 1
            if opp.get("status") == "revenue_ready":
                connector_stats[connector]["revenue_ready"] += 1
            if opp.get("status") in ("contacted", "replied", "meeting", "proposal", "negotiation"):
                connector_stats[connector]["contacted"] += 1

        # Calculate rates
        for connector, stats in connector_stats.items():
            total = stats["total"]
            stats["acceptance_rate"] = round(stats["revenue_ready"] / max(total, 1), 3)
            stats["contact_rate"] = round(stats["contacted"] / max(total, 1), 3)

        return connector_stats

    def analyze_signals(
        self,
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze signal types."""
        signal_stats: dict[str, dict[str, int]] = {}

        for opp in opportunities:
            signal = opp.get("buying_signal", "unknown")
            if signal not in signal_stats:
                signal_stats[signal] = {"total": 0, "won": 0}
            signal_stats[signal]["total"] += 1
            if opp.get("status") == "won":
                signal_stats[signal]["won"] += 1

        # Calculate win rates
        for signal, stats in signal_stats.items():
            total = stats["total"]
            stats["win_rate"] = round(stats["won"] / max(total, 1), 3)

        return signal_stats

    def get_insights(
        self,
        opportunities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate actionable insights."""
        insights = []

        # Check for bottlenecks
        pipeline = self.analyze_pipeline(opportunities)
        for stage, count in pipeline.get("by_stage", {}).items():
            concentration = count / max(pipeline["total"], 1)
            if concentration > 0.3:
                insights.append({
                    "type": "bottleneck",
                    "severity": "high" if concentration > 0.5 else "medium",
                    "message": f"{concentration:.0%} of opportunities stuck at {stage}",
                    "action": f"Review {stage} opportunities",
                })

        # Check connector performance
        connectors = self.analyze_connectors(opportunities)
        for connector, stats in connectors.items():
            if stats["acceptance_rate"] < 0.1:
                insights.append({
                    "type": "connector_performance",
                    "severity": "medium",
                    "message": f"{connector} has low acceptance rate ({stats['acceptance_rate']:.0%})",
                    "action": f"Investigate {connector} signals",
                })

        return insights
