"""Git-history style lead timeline assembly — deterministic, no AI."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def sort_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        events,
        key=lambda e: (
            e.get("occurred_at") or e.get("created_at") or "",
            e.get("sequence") or 0,
        ),
    )


def format_timeline_label(event_type: str, detail: str = "") -> str:
    label = (event_type or "event").replace("_", " ").strip()
    if detail:
        return f"{label}: {detail}"
    return label


def serialize_timeline_event(row: dict[str, Any]) -> dict[str, Any]:
    occurred = row.get("occurred_at")
    if isinstance(occurred, datetime):
        occurred_iso = occurred.isoformat()
    else:
        occurred_iso = str(occurred or "")
    return {
        "id": str(row.get("id") or ""),
        "event_type": row.get("event_type") or "",
        "label": format_timeline_label(str(row.get("event_type") or ""), str(row.get("headline") or "")),
        "headline": row.get("headline") or "",
        "detail": row.get("detail") or "",
        "stage": row.get("stage"),
        "status": row.get("status"),
        "connector": row.get("connector"),
        "provider": row.get("provider"),
        "occurred_at": occurred_iso,
        "payload": row.get("payload") or {},
    }


def build_replay_frames(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Animate Signal → Company → Email → Founder → Revenue Ready."""
    frames: list[dict[str, Any]] = []
    cumulative: list[dict[str, Any]] = []
    for idx, event in enumerate(sort_timeline(events)):
        cumulative.append(serialize_timeline_event(event))
        frames.append(
            {
                "index": idx,
                "at": serialize_timeline_event(event)["occurred_at"],
                "focus": serialize_timeline_event(event),
                "events_so_far": list(cumulative),
            }
        )
    return frames
