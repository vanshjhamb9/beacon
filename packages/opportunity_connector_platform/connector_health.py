"""Connector health engine.

Every minute calculate: Healthy / Warning / Critical / Offline
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class HealthInput:
    latency_ms: float = 0.0
    failures: int = 0
    retries: int = 0
    authenticated: bool = True
    rate_limit_remaining: int | None = None
    queue_size: int = 0
    freshness_minutes: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    consecutive_failures: int = 0


class ConnectorHealthEngine:
    """Deterministic health classification."""

    def calculate(self, row: HealthInput) -> dict[str, object]:
        status = self._classify(row)
        return {
            "status": status,
            "latency_ms": row.latency_ms,
            "failures": row.failures,
            "retries": row.retries,
            "authenticated": row.authenticated,
            "rate_limit_remaining": row.rate_limit_remaining,
            "queue_size": row.queue_size,
            "freshness_minutes": row.freshness_minutes,
            "consecutive_failures": row.consecutive_failures,
            "last_success": row.last_success.isoformat() if row.last_success else None,
            "last_failure": row.last_failure.isoformat() if row.last_failure else None,
        }

    def _classify(self, row: HealthInput) -> str:
        if not row.authenticated:
            return "critical"
        if row.failures >= 10:
            return "critical"
        if row.consecutive_failures >= 5:
            return "critical"
        if row.latency_ms <= 0 and row.freshness_minutes > 240:
            return "offline"
        if row.rate_limit_remaining is not None and row.rate_limit_remaining == 0:
            return "warning"
        if row.queue_size > 1000:
            return "warning"
        if row.freshness_minutes > 120:
            return "warning"
        if row.latency_ms > 30000:
            return "warning"
        return "healthy"

    def bulk_calculate(self, inputs: dict[str, HealthInput]) -> dict[str, dict[str, object]]:
        return {cid: self.calculate(inp) for cid, inp in inputs.items()}

    def worst_status(self, statuses: list[str]) -> str:
        priority = {"critical": 0, "warning": 1, "offline": 2, "healthy": 3}
        if not statuses:
            return "healthy"
        return min(statuses, key=lambda s: priority.get(s, 4))
