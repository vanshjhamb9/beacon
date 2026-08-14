"""Scheduler Monitor — tracks scheduled worker execution."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class SchedulerEntry:
    """Single scheduler entry."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.worker_name: str = data.get("worker_name", "unknown")
        self.collector: str = data.get("collector", "unknown")
        self.last_run: datetime | None = data.get("last_run")
        self.next_run: datetime | None = data.get("next_run")
        self.avg_runtime: float = data.get("avg_runtime", 0.0)
        self.success_rate: float = data.get("success_rate", 0.0)
        self.failure_rate: float = data.get("failure_rate", 0.0)
        self.retries: int = data.get("retries", 0)
        self.queue_position: int = data.get("queue_position", 0)
        self.status: str = data.get("status", "idle")
        self.enabled: bool = data.get("enabled", True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "worker_name": self.worker_name,
            "collector": self.collector,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "avg_runtime": self.avg_runtime,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "retries": self.retries,
            "queue_position": self.queue_position,
            "status": self.status,
            "enabled": self.enabled,
        }


class SchedulerMonitor:
    """Tracks scheduled worker execution."""

    def __init__(self):
        self._entries: dict[str, SchedulerEntry] = {}
        self._history: list[dict[str, Any]] = []

    def register_worker(
        self,
        worker_name: str,
        collector: str,
        schedule: str = "hourly",
    ) -> SchedulerEntry:
        """Register a scheduled worker."""
        entry = SchedulerEntry({
            "worker_name": worker_name,
            "collector": collector,
        })
        self._entries[worker_name] = entry
        return entry

    def record_execution(
        self,
        worker_name: str,
        duration: float,
        success: bool,
    ):
        """Record worker execution."""
        if worker_name in self._entries:
            entry = self._entries[worker_name]
            entry.last_run = datetime.now(timezone.utc)
            entry.status = "idle" if success else "failed"
            self._history.append({
                "worker": worker_name,
                "duration": duration,
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    def get_entry(self, worker_name: str) -> SchedulerEntry | None:
        """Get scheduler entry."""
        return self._entries.get(worker_name)

    def get_all_entries(self) -> list[SchedulerEntry]:
        """Get all scheduler entries."""
        return list(self._entries.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics."""
        total = len(self._entries)
        enabled = sum(1 for e in self._entries.values() if e.enabled)
        failed = sum(1 for e in self._entries.values() if e.status == "failed")

        return {
            "total_workers": total,
            "enabled": enabled,
            "failed": failed,
            "total_executions": len(self._history),
        }
