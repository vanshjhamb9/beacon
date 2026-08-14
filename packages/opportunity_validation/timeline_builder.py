"""Timeline builder — constructs chronological event history for every opportunity.

Answer: What happened and when?

Every opportunity automatically builds a timeline.
No timeline = cannot become Revenue Ready.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

from .v1_schemas import TimelineEvent


class TimelineBuilder:
    """Builds chronological event history for opportunities."""

    def __init__(self):
        self._timelines: dict[str, list[dict[str, Any]]] = {}

    def add_event(
        self,
        opportunity_id: str,
        event_type: str,
        description: str,
        source: str,
        connector: str,
        timestamp: datetime | None = None,
        confidence: float = 1.0,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add event to opportunity timeline."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        event = TimelineEvent(
            data={
                "timestamp": timestamp,
                "event_type": event_type,
                "description": description,
                "source": source,
                "connector": connector,
                "confidence": confidence,
            }
        )

        if opportunity_id not in self._timelines:
            self._timelines[opportunity_id] = []

        event_dict = event.to_dict()
        event_dict["evidence"] = evidence or {}
        self._timelines[opportunity_id].append(event_dict)

        # Sort by timestamp
        self._timelines[opportunity_id].sort(
            key=lambda x: x.get("timestamp", "")
        )

        return event_dict

    def build_timeline_from_signals(
        self,
        opportunity_id: str,
        signals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build timeline from signal data."""
        for signal in signals:
            self.add_event(
                opportunity_id=opportunity_id,
                event_type=signal.get("event_type", "signal"),
                description=signal.get("description", "Unknown event"),
                source=signal.get("source", "unknown"),
                connector=signal.get("connector", "unknown"),
                timestamp=signal.get("timestamp"),
                confidence=signal.get("confidence", 1.0),
                evidence=signal.get("evidence"),
            )

        return self.get_timeline(opportunity_id)

    def get_timeline(self, opportunity_id: str) -> list[dict[str, Any]]:
        """Get full timeline for opportunity."""
        return self._timelines.get(opportunity_id, [])

    def get_timeline_length(self, opportunity_id: str) -> int:
        """Get number of events in timeline."""
        return len(self._timelines.get(opportunity_id, []))

    def get_first_event(self, opportunity_id: str) -> dict[str, Any] | None:
        """Get first event in timeline."""
        timeline = self._timelines.get(opportunity_id, [])
        return timeline[0] if timeline else None

    def get_last_event(self, opportunity_id: str) -> dict[str, Any] | None:
        """Get last event in timeline."""
        timeline = self._timelines.get(opportunity_id, [])
        return timeline[-1] if timeline else None

    def get_event_span_days(self, opportunity_id: str) -> int:
        """Get days between first and last event."""
        timeline = self._timelines.get(opportunity_id, [])
        if len(timeline) < 2:
            return 0

        first_ts = timeline[0].get("timestamp", "")
        last_ts = timeline[-1].get("timestamp", "")

        try:
            first_dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            delta = last_dt - first_dt
            return delta.days
        except (ValueError, AttributeError):
            return 0

    def get_event_types(self, opportunity_id: str) -> list[str]:
        """Get unique event types in timeline."""
        timeline = self._timelines.get(opportunity_id, [])
        return list(set(e.get("event_type", "unknown") for e in timeline))

    def get_connectors_involved(self, opportunity_id: str) -> list[str]:
        """Get unique connectors that contributed to timeline."""
        timeline = self._timelines.get(opportunity_id, [])
        return list(set(e.get("connector", "unknown") for e in timeline))

    def has_timeline(self, opportunity_id: str) -> bool:
        """Check if opportunity has a timeline."""
        return opportunity_id in self._timelines and len(self._timelines[opportunity_id]) > 0

    def get_all_timelines(self) -> dict[str, list[dict[str, Any]]]:
        """Get all timelines."""
        return dict(self._timelines)

    def get_statistics(self) -> dict[str, Any]:
        """Get timeline statistics."""
        total_timelines = len(self._timelines)
        total_events = sum(len(events) for events in self._timelines.values())
        avg_events = total_events / total_timelines if total_timelines > 0 else 0

        event_types = {}
        connectors = {}
        for events in self._timelines.values():
            for event in events:
                event_type = event.get("event_type", "unknown")
                connector = event.get("connector", "unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1
                connectors[connector] = connectors.get(connector, 0) + 1

        return {
            "total_timelines": total_timelines,
            "total_events": total_events,
            "avg_events_per_timeline": round(avg_events, 2),
            "event_types": event_types,
            "connectors": connectors,
        }

    def clear(self):
        """Clear all timelines (for testing)."""
        self._timelines.clear()
