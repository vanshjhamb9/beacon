"""Collector activity helpers for ingestion events."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def summarize_collector_activity(
    events: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Aggregate append-only ingestion events by collector."""
    summary: dict[str, dict[str, Any]] = {}
    for event in events:
        collector = str(event.get("collector") or "unknown")
        bucket = summary.setdefault(
            collector,
            {
                "success": 0,
                "failure": 0,
                "total": 0,
                "duration_sum": 0.0,
                "duration_n": 0,
                "last_run": None,
                "last_success": None,
                "last_failure": None,
                "reasons": {},
            },
        )
        status = str(event.get("status") or "").lower()
        bucket["total"] += 1
        created = event.get("created_at")
        if isinstance(created, datetime):
            if bucket["last_run"] is None or created > bucket["last_run"]:
                bucket["last_run"] = created
        duration = event.get("duration")
        if isinstance(duration, (int, float)):
            bucket["duration_sum"] += float(duration)
            bucket["duration_n"] += 1
        if status in {"ok", "success", "collected", "admitted", "recovered", "promoted"}:
            bucket["success"] += 1
            if isinstance(created, datetime):
                if bucket["last_success"] is None or created > bucket["last_success"]:
                    bucket["last_success"] = created
        else:
            bucket["failure"] += 1
            reason = str(event.get("reason") or status or "unknown")
            reasons: dict[str, int] = bucket["reasons"]
            reasons[reason] = reasons.get(reason, 0) + 1
            if isinstance(created, datetime):
                if bucket["last_failure"] is None or created > bucket["last_failure"]:
                    bucket["last_failure"] = created
    for bucket in summary.values():
        total = max(int(bucket["total"]), 1)
        bucket["success_rate"] = round(bucket["success"] / total * 100.0, 1)
        if bucket["duration_n"]:
            bucket["avg_runtime"] = round(bucket["duration_sum"] / bucket["duration_n"], 2)
        else:
            bucket["avg_runtime"] = 0.0
    return summary


def top_failure_reasons(
    events: list[dict[str, Any]],
    *,
    limit: int = 10,
) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for event in events:
        status = str(event.get("status") or "").lower()
        if status in {"ok", "success", "collected", "admitted", "recovered", "promoted"}:
            continue
        reason = str(event.get("reason") or status or "unknown").strip() or "unknown"
        counts[reason] = counts.get(reason, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:limit]
