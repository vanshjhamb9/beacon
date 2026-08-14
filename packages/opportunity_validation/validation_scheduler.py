"""Validation scheduler — runs periodic validation on opportunities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class ValidationScheduler:
    """Schedules and runs periodic validation on opportunities."""

    def __init__(self):
        self._schedules: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def schedule_validation(
        self,
        schedule_id: str,
        frequency: str,
        opportunity_ids: list[str],
        validator_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Schedule validation run."""
        schedule = {
            "schedule_id": schedule_id,
            "frequency": frequency,
            "opportunity_ids": opportunity_ids,
            "validator_config": validator_config or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run": None,
            "next_run": None,
            "run_count": 0,
            "status": "active",
        }

        self._schedules[schedule_id] = schedule
        return schedule

    def run_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Run scheduled validation."""
        if schedule_id not in self._schedules:
            return {"error": "Schedule not found"}

        schedule = self._schedules[schedule_id]
        schedule["last_run"] = datetime.now(timezone.utc).isoformat()
        schedule["run_count"] += 1

        result = {
            "schedule_id": schedule_id,
            "run_at": schedule["last_run"],
            "opportunity_count": len(schedule["opportunity_ids"]),
            "status": "completed",
        }

        self._history.append(result)
        return result

    def get_schedule(self, schedule_id: str) -> dict[str, Any] | None:
        """Get schedule."""
        return self._schedules.get(schedule_id)

    def get_all_schedules(self) -> list[dict[str, Any]]:
        """Get all schedules."""
        return list(self._schedules.values())

    def get_active_schedules(self) -> list[dict[str, Any]]:
        """Get active schedules."""
        return [
            schedule for schedule in self._schedules.values()
            if schedule.get("status") == "active"
        ]

    def deactivate_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Deactivate schedule."""
        if schedule_id not in self._schedules:
            return {"error": "Schedule not found"}

        self._schedules[schedule_id]["status"] = "inactive"
        return {"schedule_id": schedule_id, "status": "inactive"}

    def get_history(self) -> list[dict[str, Any]]:
        """Get validation run history."""
        return list(self._history)

    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics."""
        total_schedules = len(self._schedules)
        active_schedules = len(self.get_active_schedules())
        total_runs = len(self._history)

        return {
            "total_schedules": total_schedules,
            "active_schedules": active_schedules,
            "total_runs": total_runs,
        }

    def clear(self):
        """Clear all schedules (for testing)."""
        self._schedules.clear()
        self._history.clear()
