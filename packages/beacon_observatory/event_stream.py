"""Event Stream — live source feed like terminal logs."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class StreamEvent:
    """Single stream event."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))
        self.source: str = data.get("source", "unknown")
        self.event_type: str = data.get("event_type", "unknown")
        self.message: str = data.get("message", "")
        self.details: dict[str, Any] = data.get("details", {})
        self.severity: str = data.get("severity", "info")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "event_type": self.event_type,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
        }


class EventStream:
    """Live source feed engine."""

    def __init__(self, max_events: int = 5000):
        self._events: list[StreamEvent] = []
        self._max_events = max_events

    def add_event(
        self,
        source: str,
        event_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        severity: str = "info",
    ) -> StreamEvent:
        """Add event to stream."""
        event = StreamEvent({
            "source": source,
            "event_type": event_type,
            "message": message,
            "details": details or {},
            "severity": severity,
        })

        self._events.insert(0, event)

        if len(self._events) > self._max_events:
            self._events = self._events[:self._max_events]

        return event

    def get_events(
        self,
        limit: int = 100,
        source: str | None = None,
        event_type: str | None = None,
        severity: str | None = None,
    ) -> list[StreamEvent]:
        """Get events with filtering."""
        events = self._events

        if source:
            events = [e for e in events if e.source == source]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]

        return events[:limit]

    def get_latest(self, count: int = 50) -> list[StreamEvent]:
        """Get latest events."""
        return self._events[:count]

    def get_statistics(self) -> dict[str, Any]:
        """Get event stream statistics."""
        total = len(self._events)
        by_source = {}
        by_type = {}
        by_severity = {}

        for event in self._events:
            by_source[event.source] = by_source.get(event.source, 0) + 1
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
            by_severity[event.severity] = by_severity.get(event.severity, 0) + 1

        return {
            "total_events": total,
            "by_source": by_source,
            "by_type": by_type,
            "by_severity": by_severity,
        }
