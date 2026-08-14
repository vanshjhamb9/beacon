"""DSIP: Observability Engine.

Tracks metrics, performance, and health of the entire DSIP system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    unit: str = ""  # ms, count, bytes, percent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict = field(default_factory=dict)


@dataclass
class DiscoveryMetrics:
    """Aggregated discovery metrics."""
    period: str = "24h"

    # Performance
    discovery_time_ms: float = 0.0
    connector_time_ms: float = 0.0
    avg_latency_ms: float = 0.0

    # Throughput
    companies_discovered: int = 0
    companies_accepted: int = 0
    companies_rejected: int = 0
    companies_duplicate: int = 0

    # Quality
    avg_quality_score: float = 0.0
    avg_confidence: float = 0.0
    qualification_rate: float = 0.0

    # Sources
    sources_used: int = 0
    source_health_avg: float = 0.0

    # Errors
    total_errors: int = 0
    error_rate: float = 0.0
    retry_rate: float = 0.0

    # Cost
    total_cost: float = 0.0
    cost_per_company: float = 0.0

    # Coverage
    coverage_percent: float = 0.0


class ObservabilityEngine:
    """Tracks metrics, performance, and health of DSIP.

    Tracks:
    - Discovery time, connector time, errors, retries
    - Success rate, coverage, source health
    - Companies discovered, accepted, rejected
    - Cost, latency, quality

    Usage:
        engine = ObservabilityEngine()
        engine.record_discovery(...)
        metrics = engine.get_metrics()
        health = engine.get_health()
    """

    def __init__(self):
        self._metrics: list[MetricPoint] = []
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def record_discovery(
        self,
        source_id: str,
        companies_found: int,
        duration_ms: float,
        success: bool,
        cost: float = 0.0,
    ) -> None:
        """Record a discovery operation."""
        self._increment_counter("discovery.total")
        self._increment_counter(f"discovery.source.{source_id}")
        self._add_to_histogram("discovery.duration_ms", duration_ms)

        if success:
            self._increment_counter("discovery.success")
            self._add_to_gauge("discovery.last_success_timestamp", datetime.utcnow().timestamp())
        else:
            self._increment_counter("discovery.failure")

        self._add_to_gauge("discovery.total_companies", companies_found)
        self._increment_counter("discovery.total_cost", cost)

        self._metrics.append(MetricPoint(
            name="discovery",
            value=companies_found,
            unit="count",
            tags={"source_id": source_id, "duration_ms": duration_ms, "success": success},
        ))

    def record_quality_check(
        self,
        company_id: str,
        quality_score: float,
        qualified: bool,
    ) -> None:
        """Record a quality check result."""
        self._increment_counter("quality.total")
        self._add_to_histogram("quality.score", quality_score)

        if qualified:
            self._increment_counter("quality.qualified")
        else:
            self._increment_counter("quality.rejected")

    def record_scoring(
        self,
        company_id: str,
        discovery_score: float,
        classification: str,
    ) -> None:
        """Record a scoring result."""
        self._increment_counter("scoring.total")
        self._add_to_histogram("scoring.score", discovery_score)
        self._increment_counter(f"scoring.classification.{classification}")

    def record_source_health(
        self,
        source_id: str,
        healthy: bool,
        latency_ms: float = 0.0,
    ) -> None:
        """Record source health status."""
        status = "healthy" if healthy else "unhealthy"
        self._increment_counter(f"source.health.{source_id}.{status}")
        if latency_ms > 0:
            self._add_to_histogram(f"source.latency.{source_id}", latency_ms)

    def get_metrics(self, period: str = "24h") -> DiscoveryMetrics:
        """Get aggregated metrics for a period."""
        metrics = DiscoveryMetrics(period=period)

        # Calculate from histograms
        metrics.avg_latency_ms = self._get_histogram_avg("discovery.duration_ms")
        metrics.avg_quality_score = self._get_histogram_avg("quality.score")
        metrics.avg_confidence = self._get_histogram_avg("scoring.score") / 100

        # Get from counters
        metrics.companies_discovered = self._counters.get("discovery.total_companies", 0)
        metrics.companies_accepted = self._counters.get("quality.qualified", 0)
        metrics.companies_rejected = self._counters.get("quality.rejected", 0)
        metrics.total_errors = self._counters.get("discovery.failure", 0)
        metrics.total_cost = self._counters.get("discovery.total_cost", 0)

        # Calculate rates
        total_discoveries = self._counters.get("discovery.total", 0)
        if total_discoveries > 0:
            metrics.error_rate = metrics.total_errors / total_discoveries * 100
            metrics.cost_per_company = metrics.total_cost / max(1, metrics.companies_discovered)

        total_quality = self._counters.get("quality.total", 0)
        if total_quality > 0:
            metrics.qualification_rate = metrics.companies_accepted / total_quality * 100

        return metrics

    def get_health(self) -> dict:
        """Get overall system health."""
        return {
            "status": "healthy",
            "uptime": "running",
            "metrics_collected": len(self._metrics),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }

    def get_source_stats(self) -> dict:
        """Get per-source statistics."""
        stats = {}
        for key, value in self._counters.items():
            if key.startswith("discovery.source."):
                source_id = key.split(".")[-1]
                stats.setdefault(source_id, {"discoveries": 0, "success": 0, "failure": 0})
                stats[source_id]["discoveries"] = value

        return stats

    def _increment_counter(self, name: str, amount: float = 1) -> None:
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + amount

    def _add_to_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        self._gauges[name] = value

    def _add_to_histogram(self, name: str, value: float) -> None:
        """Add a value to a histogram."""
        self._histograms.setdefault(name, []).append(value)
        # Keep only last 1000 values
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]

    def _get_histogram_avg(self, name: str) -> float:
        """Get average of a histogram."""
        values = self._histograms.get(name, [])
        return sum(values) / len(values) if values else 0.0

    def _get_histogram_p95(self, name: str) -> float:
        """Get 95th percentile of a histogram."""
        values = sorted(self._histograms.get(name, []))
        if not values:
            return 0.0
        idx = int(len(values) * 0.95)
        return values[min(idx, len(values) - 1)]
