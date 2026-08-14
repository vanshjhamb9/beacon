"""Celery worker health normalization."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from operations_center.models import KNOWN_WORKERS, WorkerHealthView


def classify_worker_name(raw: str) -> str:
    key = (raw or "").lower()
    mapping = (
        ("collector", "collector"),
        ("collect", "collector"),
        ("identity", "identity"),
        ("igf", "identity"),
        ("erowd", "identity"),
        ("enrich", "enrichment"),
        ("decision", "decision_maker"),
        ("sales_readiness", "sales_readiness"),
        ("sales-readiness", "sales_readiness"),
        ("revenue_ready", "revenue_ready"),
        ("revenue-ready", "revenue_ready"),
        ("rrp", "revenue_ready"),
        ("outreach", "outreach"),
        ("ofc", "outreach"),
        ("communication", "outreach"),
    )
    for needle, name in mapping:
        if needle in key:
            return name
    return key.split(".")[0] or "unknown"


def build_worker_views(
    *,
    inspect_payload: dict[str, Any] | None = None,
    queue_sizes: dict[str, int] | None = None,
    stats: dict[str, dict[str, Any]] | None = None,
) -> list[WorkerHealthView]:
    inspect_payload = inspect_payload or {}
    queue_sizes = queue_sizes or {}
    stats = stats or {}

    ping = inspect_payload.get("ping") or {}
    active = inspect_payload.get("active") or {}
    worker_online = bool(ping)

    by_name: dict[str, WorkerHealthView] = {}
    for name in KNOWN_WORKERS:
        st = stats.get(name, {})
        queue_size = int(queue_sizes.get(name, 0) or 0)
        running = worker_online
        status = "running" if running else "offline"
        if running and queue_size == 0 and not _has_active(active, name):
            status = "idle"
        by_name[name] = WorkerHealthView(
            worker_name=name,
            running=running,
            queue_size=queue_size,
            jobs_completed=int(st.get("jobs_completed", 0) or 0),
            jobs_failed=int(st.get("jobs_failed", 0) or 0),
            avg_duration=float(st.get("avg_duration", 0.0) or 0.0),
            last_execution=_as_dt(st.get("last_execution")),
            status=status,
        )
    return [by_name[name] for name in KNOWN_WORKERS]


def _has_active(active: dict[str, Any], worker_name: str) -> bool:
    for tasks in active.values():
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            name = str((task or {}).get("name") or "")
            if classify_worker_name(name) == worker_name:
                return True
    return False


def _as_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
