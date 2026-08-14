"""Connector Runtime — tracks connector execution history."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ConnectorExecution:
    """Single connector execution record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.connector_name: str = data.get("connector_name", "unknown")
        self.execution_number: int = data.get("execution_number", 0)
        self.started_at: datetime = data.get("started_at", datetime.now(timezone.utc))
        self.finished_at: datetime | None = data.get("finished_at")
        self.duration_seconds: float = data.get("duration_seconds", 0.0)
        self.signals_fetched: int = data.get("signals_fetched", 0)
        self.accepted: int = data.get("accepted", 0)
        self.rejected: int = data.get("rejected", 0)
        self.revenue_ready: int = data.get("revenue_ready", 0)
        self.failure: str = data.get("failure", "")
        self.logs: list[str] = data.get("logs", [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connector_name": self.connector_name,
            "execution_number": self.execution_number,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "signals_fetched": self.signals_fetched,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "revenue_ready": self.revenue_ready,
            "failure": self.failure,
            "logs": self.logs,
        }


class ConnectorRuntime:
    """Tracks connector execution history."""

    def __init__(self, retention_days: int = 90):
        self._executions: dict[str, list[ConnectorExecution]] = {}
        self._execution_counters: dict[str, int] = {}
        self._retention_days = retention_days

    def record_execution(
        self,
        connector_name: str,
        signals_fetched: int,
        accepted: int,
        rejected: int,
        revenue_ready: int,
        duration: float,
        failure: str = "",
        logs: list[str] | None = None,
    ) -> ConnectorExecution:
        """Record connector execution."""
        if connector_name not in self._execution_counters:
            self._execution_counters[connector_name] = 0
        self._execution_counters[connector_name] += 1

        execution = ConnectorExecution({
            "connector_name": connector_name,
            "execution_number": self._execution_counters[connector_name],
            "started_at": datetime.now(timezone.utc),
            "finished_at": datetime.now(timezone.utc),
            "duration_seconds": duration,
            "signals_fetched": signals_fetched,
            "accepted": accepted,
            "rejected": rejected,
            "revenue_ready": revenue_ready,
            "failure": failure,
            "logs": logs or [],
        })

        if connector_name not in self._executions:
            self._executions[connector_name] = []
        self._executions[connector_name].append(execution)

        return execution

    def get_executions(self, connector_name: str, limit: int = 50) -> list[ConnectorExecution]:
        """Get executions for connector."""
        executions = self._executions.get(connector_name, [])
        return executions[-limit:]

    def get_all_executions(self, limit: int = 100) -> list[ConnectorExecution]:
        """Get all recent executions."""
        all_executions = []
        for executions in self._executions.values():
            all_executions.extend(executions)
        all_executions.sort(key=lambda e: e.started_at, reverse=True)
        return all_executions[:limit]

    def get_statistics(self, connector_name: str | None = None) -> dict[str, Any]:
        """Get connector statistics."""
        if connector_name:
            executions = self._executions.get(connector_name, [])
            return self._calc_stats(connector_name, executions)

        stats = {}
        for name, executions in self._executions.items():
            stats[name] = self._calc_stats(name, executions)
        return stats

    def _calc_stats(self, name: str, executions: list[ConnectorExecution]) -> dict[str, Any]:
        """Calculate statistics for executions."""
        total = len(executions)
        if total == 0:
            return {"name": name, "total_executions": 0}

        successful = sum(1 for e in executions if not e.failure)
        failed = sum(1 for e in executions if e.failure)
        total_signals = sum(e.signals_fetched for e in executions)
        total_accepted = sum(e.accepted for e in executions)
        total_revenue_ready = sum(e.revenue_ready for e in executions)
        avg_duration = sum(e.duration_seconds for e in executions) / total

        return {
            "name": name,
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total, 3),
            "total_signals": total_signals,
            "total_accepted": total_accepted,
            "total_revenue_ready": total_revenue_ready,
            "avg_duration": round(avg_duration, 2),
        }
