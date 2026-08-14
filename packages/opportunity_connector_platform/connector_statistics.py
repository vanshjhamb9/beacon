"""Connector statistics rollups."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ConnectorStatistics:
    """Aggregate connector events into summary statistics."""

    def summarize(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "signals": len(events),
            "accepted": sum(1 for event in events if event.get("accepted")),
            "rejected": sum(1 for event in events if not event.get("accepted")),
            "acceptance_rate": self._rate(
                sum(1 for event in events if event.get("accepted")),
                len(events),
            ),
            "top_event_types": dict(
                Counter(str(event.get("event_type") or "Unknown") for event in events).most_common(10)
            ),
            "top_companies": dict(
                Counter(str(event.get("company_name") or "Unknown") for event in events).most_common(10)
            ),
            "top_rejections": dict(
                Counter(
                    str(event.get("rejection_reason") or "accepted")
                    for event in events
                    if not event.get("accepted")
                ).most_common(10)
            ),
            "top_connectors": dict(
                Counter(str(event.get("connector_id") or "Unknown") for event in events).most_common(10)
            ),
        }

    def by_connector(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        by_id: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            cid = str(event.get("connector_id") or "unknown")
            by_id.setdefault(cid, []).append(event)
        return {cid: self.summarize(evts) for cid, evts in by_id.items()}

    def by_event_type(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        by_type: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            etype = str(event.get("event_type") or "unknown")
            by_type.setdefault(etype, []).append(event)
        return {etype: self.summarize(evts) for etype, evts in by_type.items()}

    def _rate(self, numerator: int, denominator: int) -> float:
        return round((numerator / denominator) * 100, 2) if denominator else 0.0
