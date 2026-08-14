"""Feed Engine — real-time event stream for opportunity discovery.

Live feed showing:
    LinkedIn Jobs → HubSpot → Hiring → DQE Passed → LOVP Approved → Revenue Ready

Auto refresh: 5 seconds
Newest first
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class FeedEvent:
    """Single feed event."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.event_type: str = data.get("event_type", "unknown")
        self.source: str = data.get("source", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.buying_signal: str = data.get("buying_signal", "unknown")
        self.stage: str = data.get("stage", "unknown")
        self.status: str = data.get("status", "unknown")
        self.quality_score: int = data.get("quality_score", 0)
        self.evidence: dict[str, Any] = data.get("evidence", {})
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source": self.source,
            "connector": self.connector,
            "company_name": self.company_name,
            "buying_signal": self.buying_signal,
            "stage": self.stage,
            "status": self.status,
            "quality_score": self.quality_score,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
        }


class FeedEngine:
    """Live discovery feed engine."""

    def __init__(self, max_events: int = 1000):
        self._events: list[FeedEvent] = []
        self._max_events = max_events

    def add_event(
        self,
        event_type: str,
        source: str,
        connector: str,
        company_name: str,
        buying_signal: str,
        stage: str,
        status: str,
        quality_score: int = 0,
        evidence: dict[str, Any] | None = None,
    ) -> FeedEvent:
        """Add event to feed."""
        event = FeedEvent({
            "event_type": event_type,
            "source": source,
            "connector": connector,
            "company_name": company_name,
            "buying_signal": buying_signal,
            "stage": stage,
            "status": status,
            "quality_score": quality_score,
            "evidence": evidence or {},
            "timestamp": datetime.now(timezone.utc),
        })

        self._events.insert(0, event)  # Newest first

        # Trim if exceeding max
        if len(self._events) > self._max_events:
            self._events = self._events[:self._max_events]

        return event

    def get_events(
        self,
        limit: int = 50,
        offset: int = 0,
        connector: str | None = None,
        event_type: str | None = None,
        company_name: str | None = None,
    ) -> list[FeedEvent]:
        """Get events with filtering."""
        events = self._events

        if connector:
            events = [e for e in events if e.connector == connector]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if company_name:
            events = [e for e in events if company_name.lower() in e.company_name.lower()]

        return events[offset:offset + limit]

    def get_latest(self, count: int = 10) -> list[FeedEvent]:
        """Get latest events."""
        return self._events[:count]

    def get_by_connector(self, connector: str) -> list[FeedEvent]:
        """Get events by connector."""
        return [e for e in self._events if e.connector == connector]

    def get_by_company(self, company_name: str) -> list[FeedEvent]:
        """Get events by company name."""
        return [e for e in self._events if company_name.lower() in e.company_name.lower()]

    def get_statistics(self) -> dict[str, Any]:
        """Get feed statistics."""
        total = len(self._events)
        by_connector = {}
        by_event_type = {}
        by_stage = {}

        for event in self._events:
            by_connector[event.connector] = by_connector.get(event.connector, 0) + 1
            by_event_type[event.event_type] = by_event_type.get(event.event_type, 0) + 1
            by_stage[event.stage] = by_stage.get(event.stage, 0) + 1

        return {
            "total_events": total,
            "by_connector": by_connector,
            "by_event_type": by_event_type,
            "by_stage": by_stage,
        }
