"""Follow-up sequence helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from comai_partner_outreach.config import PartnerOutreachConfig


STEP_ORDER = ("intro", "fu1", "fu2", "final")


def step_day_offsets(config: PartnerOutreachConfig) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in config.sequence_steps:
        step = str(item.get("step") or "")
        if step:
            out[step] = int(item.get("day_offset") or 0)
    if not out:
        out = {"intro": 0, "fu1": 3, "fu2": 7, "final": 14}
    return out


def next_step_after(current: str) -> str | None:
    current = (current or "").lower()
    if current not in STEP_ORDER:
        return "fu1" if current == "intro" or not current else None
    idx = STEP_ORDER.index(current)
    if idx + 1 >= len(STEP_ORDER):
        return None
    return STEP_ORDER[idx + 1]


def schedule_after_step(
    step: str,
    config: PartnerOutreachConfig,
    *,
    now: datetime | None = None,
) -> datetime | None:
    """Return next_followup_at after successfully sending `step`."""
    nxt = next_step_after(step)
    if not nxt:
        return None
    offsets = step_day_offsets(config)
    now = now or datetime.now(UTC)
    current_offset = offsets.get(step, 0)
    next_offset = offsets.get(nxt, current_offset + 3)
    delta_days = max(1, next_offset - current_offset)
    return now + timedelta(days=delta_days)


def is_followup_due(lead: dict[str, Any], *, now: datetime | None = None) -> bool:
    if lead.get("stop_reason"):
        return False
    stage = (lead.get("stage") or "").lower()
    if stage not in ("sent", "nurture", "queued"):
        return False
    nxt = lead.get("next_followup_at")
    if not nxt:
        return False
    now = now or datetime.now(UTC)
    try:
        due = datetime.fromisoformat(str(nxt).replace("Z", "+00:00"))
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
    except ValueError:
        return False
    return due <= now
