"""Queue depth helpers."""

from __future__ import annotations

from typing import Any

from operations_center.models import KNOWN_QUEUES, QueueView


def build_queue_views(sizes: dict[str, int] | None = None) -> list[QueueView]:
    sizes = sizes or {}
    out: list[QueueView] = []
    for name in KNOWN_QUEUES:
        out.append(QueueView(name=name, pending=int(sizes.get(name, 0) or 0)))
    for name, pending in sizes.items():
        if name not in KNOWN_QUEUES:
            out.append(QueueView(name=name, pending=int(pending or 0)))
    return out


def estimate_queue_sizes_from_celery(inspect_payload: dict[str, Any] | None = None) -> dict[str, int]:
    """Best-effort queue sizes from Celery inspect reserved/scheduled/active."""
    inspect_payload = inspect_payload or {}
    sizes = {name: 0 for name in KNOWN_QUEUES}
    for bucket_name in ("active", "reserved", "scheduled"):
        bucket = inspect_payload.get(bucket_name) or {}
        for tasks in bucket.values():
            if not isinstance(tasks, list):
                continue
            for task in tasks:
                name = str((task or {}).get("name") or "").lower()
                mapped = _map_task_to_queue(name)
                sizes[mapped] = sizes.get(mapped, 0) + 1
    return sizes


def _map_task_to_queue(task_name: str) -> str:
    if any(k in task_name for k in ("identity", "igf", "erowd", "company_resolution")):
        return "identity"
    if any(k in task_name for k in ("enrich", "email", "contact")):
        return "email" if "email" in task_name or "contact" in task_name else "enrichment"
    if "decision" in task_name:
        return "decision"
    if any(k in task_name for k in ("revenue", "rrp", "sales_readiness")):
        return "revenue"
    return "default"
