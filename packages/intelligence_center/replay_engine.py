"""Pipeline replay frames and intelligence heatmap."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from intelligence_center.models import HeatmapCell, ReplayFrame


def build_replay_frame(
    *,
    hour: str,
    timestamp: datetime,
    counters: dict[str, int],
    movements: list[dict[str, Any]] | None = None,
) -> ReplayFrame:
    return ReplayFrame(
        hour=hour,
        timestamp=timestamp,
        signals=int(counters.get("signals", 0) or 0),
        companies=int(counters.get("companies", 0) or 0),
        websites=int(counters.get("websites", 0) or 0),
        emails=int(counters.get("emails", 0) or 0),
        decision_makers=int(counters.get("decision_makers", 0) or 0),
        sales_ready=int(counters.get("sales_ready", 0) or 0),
        revenue_ready=int(counters.get("revenue_ready", 0) or 0),
        contacted=int(counters.get("contacted", 0) or 0),
        movements=list(movements or []),
    )


def heatmap_tone(*, success_pct: float, failures: int, count: int) -> str:
    if count <= 0:
        return "yellow"
    if failures > 0 and success_pct < 50:
        return "red"
    if success_pct >= 80 and failures == 0:
        return "green"
    if success_pct >= 50:
        return "yellow"
    return "red"


def build_heatmap(rows: list[dict[str, Any]]) -> list[HeatmapCell]:
    """
    Each row: {stage, count, success_pct, avg_duration, failures}
    """
    order = [
        "collector",
        "company",
        "website",
        "email",
        "decision_maker",
        "revenue_ready",
    ]
    by_stage = {str(r.get("stage")): r for r in rows}
    cells: list[HeatmapCell] = []
    for stage in order:
        row = by_stage.get(stage, {})
        count = int(row.get("count", 0) or 0)
        success = float(row.get("success_pct", 0.0) or 0.0)
        failures = int(row.get("failures", 0) or 0)
        cells.append(
            HeatmapCell(
                stage=stage,
                tone=heatmap_tone(success_pct=success, failures=failures, count=count),
                count=count,
                success_pct=round(success, 1),
                avg_duration=float(row.get("avg_duration", 0.0) or 0.0),
                failures=failures,
            )
        )
    return cells
