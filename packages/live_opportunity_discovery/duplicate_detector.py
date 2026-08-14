"""Merge duplicate reports of the same buying event."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from live_opportunity_discovery.company_resolver import CompanyResolver
from live_opportunity_discovery.discovery_router import LiveEvent, LiveEvidence


@dataclass(frozen=True, slots=True)
class EventFingerprint:
    normalized_company: str
    category: str
    event_type: str
    week: str


class DuplicateDetector:
    def __init__(self, resolver: CompanyResolver | None = None) -> None:
        self.resolver = resolver or CompanyResolver()

    def fingerprint(self, event: LiveEvent, *, category: str, event_type: str) -> EventFingerprint:
        return EventFingerprint(
            normalized_company=self.resolver.normalize(event.company_name),
            category=category,
            event_type=event_type,
            week=self._week(event.event_timestamp),
        )

    def merge(self, events: list[LiveEvent], *, category: str, event_type: str) -> LiveEvent:
        if not events:
            raise ValueError("Cannot merge an empty event list.")
        primary = min(events, key=lambda event: event.event_timestamp)
        evidence_by_key: dict[tuple[str, str], LiveEvidence] = {}
        for event in events:
            for item in event.evidence:
                evidence_by_key[(item.source.lower(), item.url.lower())] = item
        return primary.model_copy(update={"evidence": tuple(evidence_by_key.values())})

    def _week(self, timestamp: datetime) -> str:
        year, week, _ = timestamp.isocalendar()
        return f"{year}-W{week:02d}"
