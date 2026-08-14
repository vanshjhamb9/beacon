from __future__ import annotations

from typing import Any

from ground_truth.models.types import CompanyTimeline, TimelineEvent, UNKNOWN


class CompanyTimelineEngine:
    """Rule 5 — evidence timeline that answers WHY NOW."""

    def build(self, payload: dict[str, Any]) -> CompanyTimeline:
        events: list[TimelineEvent] = []
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                events.append(
                    TimelineEvent(
                        date=row.get("date") or row.get("timestamp") or row.get("at"),
                        event=str(row.get("event") or row.get("summary") or row.get("signal_type") or UNKNOWN),
                        source=str(row.get("source") or payload.get("source") or UNKNOWN),
                        confidence=float(row["confidence"]) if row.get("confidence") is not None else None,
                        evidence=["timeline"],
                    )
                )
        for item in payload.get("evidence") or []:
            if isinstance(item, dict) and (item.get("summary") or item.get("event")):
                events.append(
                    TimelineEvent(
                        date=item.get("date") or item.get("collected_at") or payload.get("collected_at"),
                        event=str(item.get("event") or item.get("summary")),
                        source=str(item.get("source") or payload.get("source") or UNKNOWN),
                        confidence=float(item["confidence"]) if item.get("confidence") is not None else 70.0,
                        evidence=["evidence"],
                    )
                )

        # Sort by date string when possible (stable)
        def sort_key(e: TimelineEvent):
            return str(e.date or "")

        events.sort(key=sort_key)
        why_now = payload.get("why_now")
        if not why_now and events:
            recent = [e.event for e in events[-3:] if e.event != UNKNOWN]
            why_now = "; ".join(recent) if recent else UNKNOWN
        if not why_now:
            why_now = UNKNOWN

        return CompanyTimeline(
            events=events[:40],
            why_now=str(why_now),
            evidence=[f"events:{len(events)}", f"why_now:{why_now != UNKNOWN}"],
        )
