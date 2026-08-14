"""Pipeline Metrics — calculates pipeline health and conversion rates.

Tracks conversion between stages, velocity, and pipeline health.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


class PipelineMetrics:
    """Calculates pipeline metrics and conversion rates."""

    def __init__(self):
        self._metrics_history: list[dict[str, Any]] = []
        self._stage_entry_times: dict[str, dict[str, datetime]] = {}
        self._stage_exit_times: dict[str, dict[str, datetime]] = {}

    def record_stage_entry(self, opportunity_id: str, stage: str):
        """Record when opportunity enters a stage."""
        if opportunity_id not in self._stage_entry_times:
            self._stage_entry_times[opportunity_id] = {}
        self._stage_entry_times[opportunity_id][stage] = datetime.now(timezone.utc)

    def record_stage_exit(self, opportunity_id: str, stage: str):
        """Record when opportunity exits a stage."""
        if opportunity_id not in self._stage_exit_times:
            self._stage_exit_times[opportunity_id] = {}
        self._stage_exit_times[opportunity_id][stage] = datetime.now(timezone.utc)

    def calculate_time_in_stage(self, opportunity_id: str, stage: str) -> float | None:
        """Calculate time (hours) spent in a stage."""
        entry = self._stage_entry_times.get(opportunity_id, {}).get(stage)
        exit_time = self._stage_exit_times.get(opportunity_id, {}).get(stage)

        if not entry:
            return None

        end = exit_time or datetime.now(timezone.utc)
        delta = end - entry
        return delta.total_seconds() / 3600

    def calculate_conversion_rate(
        self,
        from_stage: str,
        to_stage: str,
        opportunities: list[dict[str, Any]],
    ) -> float:
        """Calculate conversion rate between stages."""
        entered_from = sum(1 for o in opportunities if o.get("stage") == from_stage)
        reached_to = sum(1 for o in opportunities if o.get("stage") == to_stage)

        if entered_from == 0:
            return 0.0
        return reached_to / entered_from

    def calculate_velocity(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate pipeline velocity."""
        total = len(opportunities)
        if total == 0:
            return {"velocity": 0, "avg_days_per_stage": 0}

        stage_counts = {}
        for opp in opportunities:
            stage = opp.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Calculate average time in pipeline
        total_days = 0
        count_with_time = 0
        for opp in opportunities:
            created = opp.get("created_at")
            if created:
                if isinstance(created, str):
                    try:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        days = (datetime.now(timezone.utc) - created_dt).days
                        total_days += days
                        count_with_time += 1
                    except ValueError:
                        pass

        avg_days = total_days / count_with_time if count_with_time > 0 else 0

        return {
            "velocity": total / max(avg_days, 1),
            "avg_days_per_stage": round(avg_days, 2),
            "total_opportunities": total,
            "stage_distribution": stage_counts,
        }

    def calculate_pipeline_health(
        self,
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate pipeline health score."""
        total = len(opportunities)
        if total == 0:
            return {"health_score": 0, "status": "empty"}

        # Count by stage
        stage_counts = {}
        for opp in opportunities:
            stage = opp.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Calculate health components
        active = stage_counts.get("contacted", 0) + stage_counts.get("replied", 0) + stage_counts.get("meeting", 0)
        won = stage_counts.get("won", 0)
        lost = stage_counts.get("lost", 0)

        # Health score: active opportunities + won - lost
        health_score = ((active / total) * 50 + (won / total) * 30 + (1 - lost / total) * 20) if total > 0 else 0

        # Determine status
        if health_score >= 70:
            status = "healthy"
        elif health_score >= 40:
            status = "warning"
        else:
            status = "critical"

        return {
            "health_score": round(health_score, 2),
            "status": status,
            "total": total,
            "active": active,
            "won": won,
            "lost": lost,
            "stage_counts": stage_counts,
        }

    def get_bottlenecks(
        self,
        opportunities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify pipeline bottlenecks."""
        stage_counts = {}
        for opp in opportunities:
            stage = opp.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        total = len(opportunities)
        if total == 0:
            return []

        bottlenecks = []
        for stage, count in stage_counts.items():
            concentration = count / total
            if concentration > 0.3:  # More than 30% in one stage
                bottlenecks.append({
                    "stage": stage,
                    "count": count,
                    "concentration": round(concentration, 3),
                    "severity": "high" if concentration > 0.5 else "medium",
                })

        return sorted(bottlenecks, key=lambda x: x["concentration"], reverse=True)

    def get_summary(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        """Get pipeline summary."""
        velocity = self.calculate_velocity(opportunities)
        health = self.calculate_pipeline_health(opportunities)
        bottlenecks = self.get_bottlenecks(opportunities)

        return {
            "velocity": velocity,
            "health": health,
            "bottlenecks": bottlenecks,
            "total_opportunities": len(opportunities),
        }
