"""Lead validator — tracks every company through the validation pipeline.

Append-only. Never overwrites. Every transition is timestamped.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import VALIDATION_STAGES
from validation_engine.models import TimelineEntry, ValidationEvent


class LeadValidator:
    """Validates and tracks lead progression through the sales pipeline."""

    def __init__(self) -> None:
        self._timelines: dict[str, list[TimelineEntry]] = {}
        self._events: list[ValidationEvent] = []

    def record_transition(
        self,
        company_id: str,
        stage: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
        confidence: float = 1.0,
    ) -> ValidationEvent:
        if stage not in VALIDATION_STAGES:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {VALIDATION_STAGES}")

        event = ValidationEvent(
            event_id=f"evt_{company_id}_{stage}_{datetime.now(UTC).timestamp()}",
            company_id=company_id,
            stage=stage,
            timestamp=datetime.now(UTC),
            evidence=evidence or {},
            source=source,
            confidence=confidence,
        )
        self._events.append(event)

        entry = TimelineEntry(
            stage=stage,
            timestamp=event.timestamp,
            evidence=event.evidence,
            source=event.source,
        )
        self._timelines.setdefault(company_id, []).append(entry)
        return event

    def get_timeline(self, company_id: str) -> list[TimelineEntry]:
        return list(self._timelines.get(company_id, []))

    def get_all_events(self) -> list[ValidationEvent]:
        return list(self._events)

    def get_events_by_stage(self, stage: str) -> list[ValidationEvent]:
        return [e for e in self._events if e.stage == stage]

    def get_events_by_company(self, company_id: str) -> list[ValidationEvent]:
        return [e for e in self._events if e.company_id == company_id]

    def get_stage_count(self, stage: str) -> int:
        return len(self.get_events_by_stage(stage))

    def get_company_stage(self, company_id: str) -> str | None:
        timeline = self._timelines.get(company_id, [])
        if not timeline:
            return None
        return timeline[-1].stage

    def get_companies_in_stage(self, stage: str) -> list[str]:
        result = []
        for company_id, timeline in self._timelines.items():
            if timeline and timeline[-1].stage == stage:
                result.append(company_id)
        return result

    def calculate_conversion_rate(self, from_stage: str, to_stage: str) -> float:
        from_count = self.get_stage_count(from_stage)
        to_count = self.get_stage_count(to_stage)
        if from_count == 0:
            return 0.0
        return (to_count / from_count) * 100.0

    def calculate_avg_time_between_stages(
        self, company_id: str, from_stage: str, to_stage: str
    ) -> float | None:
        timeline = self._timelines.get(company_id, [])
        from_entry = None
        to_entry = None
        for entry in timeline:
            if entry.stage == from_stage:
                from_entry = entry
            elif entry.stage == to_stage and from_entry is not None:
                to_entry = entry
                break
        if from_entry is None or to_entry is None:
            return None
        delta = to_entry.timestamp - from_entry.timestamp
        return delta.total_seconds()

    def get_funnel(self) -> list[dict[str, Any]]:
        funnel = []
        previous_count = 0
        for stage in VALIDATION_STAGES:
            count = self.get_stage_count(stage)
            conversion = 0.0
            drop_off = 0.0
            if previous_count > 0:
                conversion = (count / previous_count) * 100.0
                drop_off = 100.0 - conversion
            funnel.append({
                "stage": stage,
                "count": count,
                "conversion_from_previous": round(conversion, 2),
                "drop_off": round(drop_off, 2),
            })
            previous_count = count
        return funnel
