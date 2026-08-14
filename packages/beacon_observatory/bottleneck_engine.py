"""Bottleneck Engine — analyzes pipeline bottlenecks."""

from datetime import datetime, timezone
from typing import Any


class BottleneckEngine:
    """Analyzes pipeline bottlenecks."""

    def __init__(self):
        self._stage_counts: dict[str, int] = {}
        self._stage_times: dict[str, list[float]] = {}

    def record_stage(self, stage: str, count: int = 1, duration: float = 0.0):
        """Record stage activity."""
        self._stage_counts[stage] = self._stage_counts.get(stage, 0) + count

        if stage not in self._stage_times:
            self._stage_times[stage] = []
        if duration > 0:
            self._stage_times[stage].append(duration)

    def analyze_bottlenecks(self) -> list[dict[str, Any]]:
        """Analyze and identify bottlenecks."""
        total = sum(self._stage_counts.values())
        if total == 0:
            return []

        bottlenecks = []
        for stage, count in self._stage_counts.items():
            concentration = count / total
            avg_time = 0
            if stage in self._stage_times and self._stage_times[stage]:
                avg_time = sum(self._stage_times[stage]) / len(self._stage_times[stage])

            if concentration > 0.2:  # More than 20% in one stage
                bottlenecks.append({
                    "stage": stage,
                    "count": count,
                    "concentration": round(concentration, 3),
                    "avg_time_seconds": round(avg_time, 2),
                    "severity": "critical" if concentration > 0.4 else "high" if concentration > 0.3 else "medium",
                })

        return sorted(bottlenecks, key=lambda x: x["concentration"], reverse=True)

    def get_conversion_rates(self) -> dict[str, float]:
        """Calculate conversion rates between stages."""
        stages = list(self._stage_counts.keys())
        if len(stages) < 2:
            return {}

        conversion_rates = {}
        for i in range(len(stages) - 1):
            from_stage = stages[i]
            to_stage = stages[i + 1]
            from_count = self._stage_counts.get(from_stage, 0)
            to_count = self._stage_counts.get(to_stage, 0)

            if from_count > 0:
                rate = to_count / from_count
                conversion_rates[f"{from_stage}_to_{to_stage}"] = round(rate, 3)

        return conversion_rates

    def get_drop_off_points(self) -> list[dict[str, Any]]:
        """Identify biggest drop-off points."""
        stages = list(self._stage_counts.keys())
        if len(stages) < 2:
            return []

        drop_offs = []
        for i in range(len(stages) - 1):
            from_stage = stages[i]
            to_stage = stages[i + 1]
            from_count = self._stage_counts.get(from_stage, 0)
            to_count = self._stage_counts.get(to_stage, 0)

            if from_count > 0:
                drop_off = from_count - to_count
                drop_off_rate = drop_off / from_count
                drop_offs.append({
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "drop_off": drop_off,
                    "drop_off_rate": round(drop_off_rate, 3),
                })

        return sorted(drop_offs, key=lambda x: x["drop_off_rate"], reverse=True)

    def get_statistics(self) -> dict[str, Any]:
        """Get bottleneck statistics."""
        total = sum(self._stage_counts.values())
        bottlenecks = self.analyze_bottlenecks()
        conversion_rates = self.get_conversion_rates()
        drop_offs = self.get_drop_off_points()

        return {
            "total_processed": total,
            "stage_counts": dict(self._stage_counts),
            "bottlenecks": bottlenecks,
            "conversion_rates": conversion_rates,
            "drop_off_points": drop_offs,
        }
