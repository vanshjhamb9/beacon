"""Latency Engine — tracks latency across pipeline stages."""

from datetime import datetime, timezone
from typing import Any


class LatencyRecord:
    """Single latency record."""

    def __init__(self, data: dict[str, Any]):
        self.stage: str = data.get("stage", "unknown")
        self.latency_ms: float = data.get("latency_ms", 0.0)
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))
        self.metadata: dict[str, Any] = data.get("metadata", {})


class LatencyEngine:
    """Tracks latency across pipeline stages."""

    def __init__(self):
        self._records: dict[str, list[LatencyRecord]] = {}
        self._stage_latencies: dict[str, list[float]] = {}

    def record_latency(
        self,
        stage: str,
        latency_ms: float,
        metadata: dict[str, Any] | None = None,
    ):
        """Record latency for a stage."""
        record = LatencyRecord({
            "stage": stage,
            "latency_ms": latency_ms,
            "metadata": metadata or {},
        })

        if stage not in self._records:
            self._records[stage] = []
        self._records[stage].append(record)

        if stage not in self._stage_latencies:
            self._stage_latencies[stage] = []
        self._stage_latencies[stage].append(latency_ms)

        # Keep only last 1000 records per stage
        if len(self._stage_latencies[stage]) > 1000:
            self._stage_latencies[stage] = self._stage_latencies[stage][-1000:]

    def get_latency(self, stage: str) -> dict[str, Any]:
        """Get latency statistics for a stage."""
        latencies = self._stage_latencies.get(stage, [])
        if not latencies:
            return {"stage": stage, "count": 0}

        return {
            "stage": stage,
            "count": len(latencies),
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "p50_ms": round(sorted(latencies)[len(latencies) // 2], 2),
            "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if len(latencies) >= 20 else None,
            "p99_ms": round(sorted(latencies)[int(len(latencies) * 0.99)], 2) if len(latencies) >= 100 else None,
        }

    def get_all_latencies(self) -> dict[str, dict[str, Any]]:
        """Get latency for all stages."""
        return {stage: self.get_latency(stage) for stage in self._stage_latencies}

    def get_total_pipeline_latency(self) -> dict[str, Any]:
        """Get total pipeline latency."""
        all_latencies = []
        for latencies in self._stage_latencies.values():
            all_latencies.extend(latencies)

        if not all_latencies:
            return {"total_count": 0}

        return {
            "total_count": len(all_latencies),
            "total_avg_ms": round(sum(all_latencies) / len(all_latencies), 2),
            "total_min_ms": round(min(all_latencies), 2),
            "total_max_ms": round(max(all_latencies), 2),
        }
