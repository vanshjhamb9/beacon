from __future__ import annotations

from datetime import UTC, datetime

from founder_os.models.types import AnalyticsEvent, AnalyticsEventType


class AnalyticsTracker:
    """Append-only in-memory event builder — persistence is API responsibility."""

    def track(
        self,
        *,
        event_type: AnalyticsEventType,
        action: str,
        actor: str = "founder",
        company_id=None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        payload: dict | None = None,
        occurred_at: datetime | None = None,
    ) -> AnalyticsEvent:
        return AnalyticsEvent(
            event_type=event_type,
            action=action,
            actor=actor,
            company_id=company_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=dict(payload or {}),
            occurred_at=occurred_at or datetime.now(UTC),
        )
