"""Runtime Engine — live runtime dashboard for all collectors."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import CollectorStatus


class CollectorRuntimeInfo:
    """Runtime information for a single collector."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.name: str = data.get("name", "unknown")
        self.status: str = data.get("status", CollectorStatus.IDLE.value)
        self.started_at: datetime | None = data.get("started_at")
        self.finished_at: datetime | None = data.get("finished_at")
        self.duration_seconds: float = data.get("duration_seconds", 0.0)
        self.signals_collected: int = data.get("signals_collected", 0)
        self.accepted: int = data.get("accepted", 0)
        self.rejected: int = data.get("rejected", 0)
        self.revenue_ready: int = data.get("revenue_ready", 0)
        self.avg_runtime: float = data.get("avg_runtime", 0.0)
        self.last_error: str = data.get("last_error", "")
        self.next_run: datetime | None = data.get("next_run")
        self.last_run: datetime | None = data.get("last_run")
        self.total_runs: int = data.get("total_runs", 0)
        self.success_rate: float = data.get("success_rate", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "signals_collected": self.signals_collected,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "revenue_ready": self.revenue_ready,
            "avg_runtime": self.avg_runtime,
            "last_error": self.last_error,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "total_runs": self.total_runs,
            "success_rate": self.success_rate,
        }


class RuntimeEngine:
    """Live runtime dashboard engine."""

    def __init__(self):
        self._collectors: dict[str, CollectorRuntimeInfo] = {}
        self._events: list[dict[str, Any]] = []

    def register_collector(self, name: str, status: str = CollectorStatus.IDLE.value) -> CollectorRuntimeInfo:
        """Register a collector."""
        info = CollectorRuntimeInfo({"name": name, "status": status})
        self._collectors[name] = info
        return info

    def update_status(self, name: str, status: str):
        """Update collector status."""
        if name in self._collectors:
            self._collectors[name].status = status
            if status == CollectorStatus.RUNNING.value:
                self._collectors[name].started_at = datetime.now(timezone.utc)

    def record_run(
        self,
        name: str,
        duration: float,
        signals: int,
        accepted: int,
        rejected: int,
        revenue_ready: int,
        error: str = "",
    ):
        """Record a collector run."""
        if name not in self._collectors:
            self.register_collector(name)

        collector = self._collectors[name]
        collector.finished_at = datetime.now(timezone.utc)
        collector.duration_seconds = duration
        collector.signals_collected = signals
        collector.accepted = accepted
        collector.rejected = rejected
        collector.revenue_ready = revenue_ready
        collector.last_error = error
        collector.last_run = datetime.now(timezone.utc)
        collector.total_runs += 1
        collector.status = CollectorStatus.IDLE.value if not error else CollectorStatus.FAILED.value

        self._events.append({
            "collector": name,
            "event": "run_completed",
            "duration": duration,
            "signals": signals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_collector(self, name: str) -> CollectorRuntimeInfo | None:
        """Get collector info."""
        return self._collectors.get(name)

    def get_all_collectors(self) -> list[CollectorRuntimeInfo]:
        """Get all collectors."""
        return list(self._collectors.values())

    def get_running(self) -> list[CollectorRuntimeInfo]:
        """Get running collectors."""
        return [c for c in self._collectors.values() if c.status == CollectorStatus.RUNNING.value]

    def get_failed(self) -> list[CollectorRuntimeInfo]:
        """Get failed collectors."""
        return [c for c in self._collectors.values() if c.status == CollectorStatus.FAILED.value]

    def get_statistics(self) -> dict[str, Any]:
        """Get runtime statistics."""
        total = len(self._collectors)
        running = sum(1 for c in self._collectors.values() if c.status == CollectorStatus.RUNNING.value)
        failed = sum(1 for c in self._collectors.values() if c.status == CollectorStatus.FAILED.value)
        total_signals = sum(c.signals_collected for c in self._collectors.values())
        total_accepted = sum(c.accepted for c in self._collectors.values())
        total_revenue_ready = sum(c.revenue_ready for c in self._collectors.values())

        return {
            "total_collectors": total,
            "running": running,
            "idle": sum(1 for c in self._collectors.values() if c.status == CollectorStatus.IDLE.value),
            "failed": failed,
            "total_signals": total_signals,
            "total_accepted": total_accepted,
            "total_revenue_ready": total_revenue_ready,
            "avg_runtime": sum(c.avg_runtime for c in self._collectors.values()) / max(total, 1),
        }

    def get_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent events."""
        return list(reversed(self._events[-limit:]))
