"""Timeline engine — builds immutable per-company timelines.

Each company gets one immutable timeline. Append-only. Never overwrite history.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import VALIDATION_STAGES
from validation_engine.models import TimelineEntry


class TimelineEngine:
    """Builds and manages immutable per-company timelines."""

    def __init__(self) -> None:
        self._timelines: dict[str, list[TimelineEntry]] = {}

    def add_event(
        self,
        company_id: str,
        stage: str,
        *,
        evidence: dict[str, Any] | None = None,
        source: str = "",
        duration_seconds: float | None = None,
    ) -> TimelineEntry:
        if stage not in VALIDATION_STAGES:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {VALIDATION_STAGES}")

        entry = TimelineEntry(
            stage=stage,
            timestamp=datetime.now(UTC),
            evidence=evidence or {},
            source=source,
            duration_seconds=duration_seconds,
        )
        self._timelines.setdefault(company_id, []).append(entry)
        return entry

    def get_timeline(self, company_id: str) -> list[TimelineEntry]:
        return list(self._timelines.get(company_id, []))

    def get_latest_stage(self, company_id: str) -> str | None:
        timeline = self._timelines.get(company_id, [])
        return timeline[-1].stage if timeline else None

    def get_stage_history(self, company_id: str) -> list[str]:
        return [entry.stage for entry in self._timelines.get(company_id, [])]

    def get_time_in_stage(self, company_id: str, stage: str) -> float | None:
        timeline = self._timelines.get(company_id, [])
        for i, entry in enumerate(timeline):
            if entry.stage == stage:
                if i + 1 < len(timeline):
                    delta = timeline[i + 1].timestamp - entry.timestamp
                    return delta.total_seconds()
                return None
        return None

    def get_total_sales_cycle(self, company_id: str) -> float | None:
        timeline = self._timelines.get(company_id, [])
        if len(timeline) < 2:
            return None
        delta = timeline[-1].timestamp - timeline[0].timestamp
        return delta.total_seconds()

    def get_avg_time_to_stage(self, stage: str) -> float | None:
        durations: list[float] = []
        for timeline in self._timelines.values():
            for i, entry in enumerate(timeline):
                if entry.stage == stage and i > 0:
                    delta = entry.timestamp - timeline[0].timestamp
                    durations.append(delta.total_seconds())
                    break
        if not durations:
            return None
        return sum(durations) / len(durations)

    def get_companies_at_stage(self, stage: str) -> list[str]:
        result = []
        for company_id, timeline in self._timelines.items():
            if timeline and timeline[-1].stage == stage:
                result.append(company_id)
        return result

    def get_companies_who_reached_stage(self, stage: str) -> list[str]:
        result = []
        for company_id, timeline in self._timelines.items():
            if any(entry.stage == stage for entry in timeline):
                result.append(company_id)
        return result

    def build_stage_summary(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for stage in VALIDATION_STAGES:
            companies = self.get_companies_at_stage(stage)
            total_who_reached = self.get_companies_who_reached_stage(stage)
            avg_time = self.get_avg_time_to_stage(stage)
            summary[stage] = {
                "current_count": len(companies),
                "total_reached": len(total_who_reached),
                "avg_time_seconds": avg_time,
                "companies": companies,
            }
        return summary
