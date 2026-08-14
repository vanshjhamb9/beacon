"""Collector Runtime — tracks collector execution history."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class CollectorRun:
    """Single collector execution record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.collector_name: str = data.get("collector_name", "unknown")
        self.started_at: datetime = data.get("started_at", datetime.now(timezone.utc))
        self.finished_at: datetime | None = data.get("finished_at")
        self.duration_seconds: float = data.get("duration_seconds", 0.0)
        self.signals_fetched: int = data.get("signals_fetched", 0)
        self.signals_normalized: int = data.get("signals_normalized", 0)
        self.buying_signals: int = data.get("buying_signals", 0)
        self.dqe_rejected: int = data.get("dqe_rejected", 0)
        self.dqe_accepted: int = data.get("dqe_accepted", 0)
        self.revenue_ready: int = data.get("revenue_ready", 0)
        self.status: str = data.get("status", "completed")
        self.error: str = data.get("error", "")
        self.logs: list[str] = data.get("logs", [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "collector_name": self.collector_name,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "signals_fetched": self.signals_fetched,
            "signals_normalized": self.signals_normalized,
            "buying_signals": self.buying_signals,
            "dqe_rejected": self.dqe_rejected,
            "dqe_accepted": self.dqe_accepted,
            "revenue_ready": self.revenue_ready,
            "status": self.status,
            "error": self.error,
            "logs": self.logs,
        }


class CollectorRuntime:
    """Tracks collector execution history."""

    def __init__(self, retention_days: int = 90):
        self._runs: dict[str, list[CollectorRun]] = {}
        self._retention_days = retention_days

    def record_run(
        self,
        collector_name: str,
        signals_fetched: int,
        signals_normalized: int,
        buying_signals: int,
        dqe_rejected: int,
        dqe_accepted: int,
        revenue_ready: int,
        duration: float,
        status: str = "completed",
        error: str = "",
    ) -> CollectorRun:
        """Record a collector execution."""
        run = CollectorRun({
            "collector_name": collector_name,
            "started_at": datetime.now(timezone.utc),
            "finished_at": datetime.now(timezone.utc),
            "duration_seconds": duration,
            "signals_fetched": signals_fetched,
            "signals_normalized": signals_normalized,
            "buying_signals": buying_signals,
            "dqe_rejected": dqe_rejected,
            "dqe_accepted": dqe_accepted,
            "revenue_ready": revenue_ready,
            "status": status,
            "error": error,
        })

        if collector_name not in self._runs:
            self._runs[collector_name] = []
        self._runs[collector_name].append(run)

        return run

    def get_runs(self, collector_name: str, limit: int = 50) -> list[CollectorRun]:
        """Get runs for a collector."""
        runs = self._runs.get(collector_name, [])
        return runs[-limit:]

    def get_all_runs(self, limit: int = 100) -> list[CollectorRun]:
        """Get all recent runs."""
        all_runs = []
        for runs in self._runs.values():
            all_runs.extend(runs)
        all_runs.sort(key=lambda r: r.started_at, reverse=True)
        return all_runs[:limit]

    def get_statistics(self, collector_name: str | None = None) -> dict[str, Any]:
        """Get collector statistics."""
        if collector_name:
            runs = self._runs.get(collector_name, [])
            return self._calc_stats(collector_name, runs)

        stats = {}
        for name, runs in self._runs.items():
            stats[name] = self._calc_stats(name, runs)
        return stats

    def _calc_stats(self, name: str, runs: list[CollectorRun]) -> dict[str, Any]:
        """Calculate statistics for runs."""
        total = len(runs)
        if total == 0:
            return {"name": name, "total_runs": 0}

        successful = sum(1 for r in runs if r.status == "completed")
        failed = sum(1 for r in runs if r.status == "failed")
        total_signals = sum(r.signals_fetched for r in runs)
        total_accepted = sum(r.dqe_accepted for r in runs)
        total_revenue_ready = sum(r.revenue_ready for r in runs)
        avg_duration = sum(r.duration_seconds for r in runs) / total

        return {
            "name": name,
            "total_runs": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total, 3),
            "total_signals": total_signals,
            "total_accepted": total_accepted,
            "total_revenue_ready": total_revenue_ready,
            "avg_duration": round(avg_duration, 2),
        }
