"""Runtime Metrics — tracks runtime performance metrics."""

from datetime import datetime, timezone
from typing import Any


class RuntimeMetrics:
    """Tracks runtime performance metrics."""

    def __init__(self):
        self._metrics: dict[str, list[dict[str, Any]]] = {}
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None):
        """Record a metric."""
        if name not in self._metrics:
            self._metrics[name] = []

        self._metrics[name].append({
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Keep only last 1000 values per metric
        if len(self._metrics[name]) > 1000:
            self._metrics[name] = self._metrics[name][-1000:]

    def increment_counter(self, name: str, value: float = 1.0):
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        self._gauges[name] = value

    def get_metric(self, name: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get metric values."""
        return self._metrics.get(name, [])[-limit:]

    def get_counter(self, name: str) -> float:
        """Get counter value."""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self._gauges.get(name, 0.0)

    def get_all_counters(self) -> dict[str, float]:
        """Get all counters."""
        return dict(self._counters)

    def get_all_gauges(self) -> dict[str, float]:
        """Get all gauges."""
        return dict(self._gauges)

    def get_statistics(self) -> dict[str, Any]:
        """Get metrics statistics."""
        return {
            "total_metrics": len(self._metrics),
            "total_counters": len(self._counters),
            "total_gauges": len(self._gauges),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }
