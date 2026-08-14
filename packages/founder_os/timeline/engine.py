from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from founder_os.models.types import FounderOsInput, TimelineEvent, TimelineStage


STAGE_ORDER = list(TimelineStage)


class RevenueTimelineEngine:
    """Immutable company revenue timeline — append-only event records."""

    def build_events(self, data: FounderOsInput) -> list[TimelineEvent]:
        now = data.now or datetime.now(UTC)
        events: list[TimelineEvent] = []
        for seed in data.timeline_seeds:
            company_id = self._uuid(seed.get("company_id"))
            if company_id is None:
                continue
            stage_raw = str(seed.get("stage") or TimelineStage.DISCOVERY.value).lower()
            try:
                stage = TimelineStage(stage_raw)
            except ValueError:
                stage = TimelineStage.DISCOVERY
            occurred = seed.get("occurred_at")
            if isinstance(occurred, datetime):
                when = occurred
            else:
                try:
                    when = datetime.fromisoformat(str(occurred).replace("Z", "+00:00")) if occurred else now
                except ValueError:
                    when = now
            events.append(
                TimelineEvent(
                    event_id=str(seed.get("event_id") or uuid4()),
                    company_id=company_id,
                    company_name=str(seed.get("company_name") or "Unknown"),
                    stage=stage,
                    occurred_at=when,
                    summary=str(seed.get("summary") or f"{stage.value} recorded"),
                    evidence=[str(e) for e in (seed.get("evidence") or [f"stage:{stage.value}"])][:10],
                    actor=str(seed.get("actor") or "system"),
                    metadata=dict(seed.get("metadata") or {}),
                    immutable=True,
                )
            )
        events.sort(key=lambda e: (e.company_name, e.occurred_at, STAGE_ORDER.index(e.stage)))
        return events

    def company_timeline(self, events: list[TimelineEvent], company_id: UUID) -> list[TimelineEvent]:
        return [e for e in events if e.company_id == company_id]

    def _uuid(self, value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError):
            return None
