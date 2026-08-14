"""Timeline Engine — tracks opportunity timeline across pipeline."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class TimelineEvent:
    """Single timeline event."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.stage: str = data.get("stage", "unknown")
        self.event_type: str = data.get("event_type", "unknown")
        self.description: str = data.get("description", "")
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))
        self.metadata: dict[str, Any] = data.get("metadata", {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "stage": self.stage,
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class TimelineEngine:
    """Tracks opportunity timeline across pipeline."""

    def __init__(self):
        self._timelines: dict[str, list[TimelineEvent]] = {}

    def add_event(
        self,
        opportunity_id: str,
        stage: str,
        event_type: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        """Add timeline event."""
        event = TimelineEvent({
            "opportunity_id": opportunity_id,
            "stage": stage,
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {},
        })

        if opportunity_id not in self._timelines:
            self._timelines[opportunity_id] = []
        self._timelines[opportunity_id].append(event)

        return event

    def get_timeline(self, opportunity_id: str) -> list[TimelineEvent]:
        """Get timeline for opportunity."""
        return self._timelines.get(opportunity_id, [])

    def get_all_timelines(self) -> dict[str, list[dict[str, Any]]]:
        """Get all timelines."""
        return {
            opp_id: [event.to_dict() for event in events]
            for opp_id, events in self._timelines.items()
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get timeline statistics."""
        total_timelines = len(self._timelines)
        total_events = sum(len(events) for events in self._timelines.values())

        return {
            "total_timelines": total_timelines,
            "total_events": total_events,
            "avg_events_per_timeline": round(total_events / max(total_timelines, 1), 2),
        }
