"""Meeting tracker — records all meeting events for companies.

Append-only. Never overwrites. Every meeting is timestamped.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from validation_engine import MEETING_TYPES
from validation_engine.models import MeetingEvent


class MeetingTracker:
    """Tracks meeting events (scheduled, completed, cancelled, no-show) for companies."""

    def __init__(self) -> None:
        self._meetings: dict[str, list[MeetingEvent]] = {}
        self._all_meetings: list[MeetingEvent] = []

    def record_meeting(
        self,
        company_id: str,
        meeting_type: str,
        *,
        duration_minutes: float | None = None,
        calendar_link: str = "",
        notes: str = "",
        next_action: str = "",
        evidence: dict[str, Any] | None = None,
    ) -> MeetingEvent:
        if meeting_type not in MEETING_TYPES:
            raise ValueError(
                f"Invalid meeting type: {meeting_type}."
                f" Must be one of {MEETING_TYPES}"
            )

        event = MeetingEvent(
            company_id=company_id,
            meeting_type=meeting_type,
            timestamp=datetime.now(UTC),
            duration_minutes=duration_minutes,
            calendar_link=calendar_link,
            notes=notes,
            next_action=next_action,
            evidence=evidence or {},
        )
        self._meetings.setdefault(company_id, []).append(event)
        self._all_meetings.append(event)
        return event

    def get_meetings_for_company(self, company_id: str) -> list[MeetingEvent]:
        return list(self._meetings.get(company_id, []))

    def get_all_meetings(self) -> list[MeetingEvent]:
        return list(self._all_meetings)

    def get_completed_meetings(self) -> list[MeetingEvent]:
        return [m for m in self._all_meetings if m.meeting_type == "completed"]

    def get_cancelled_meetings(self) -> list[MeetingEvent]:
        return [m for m in self._all_meetings if m.meeting_type == "cancelled"]

    def get_no_shows(self) -> list[MeetingEvent]:
        return [m for m in self._all_meetings if m.meeting_type == "no_show"]

    def get_scheduled_meetings(self) -> list[MeetingEvent]:
        return [m for m in self._all_meetings if m.meeting_type == "scheduled"]

    def get_meeting_rate(self) -> float:
        if not self._all_meetings:
            return 0.0
        completed = len(self.get_completed_meetings())
        return (completed / len(self._all_meetings)) * 100.0

    def get_avg_duration(self) -> float | None:
        durations = [
            m.duration_minutes
            for m in self._all_meetings
            if m.duration_minutes is not None
        ]
        if not durations:
            return None
        return sum(durations) / len(durations)

    def get_no_show_rate(self) -> float:
        if not self._all_meetings:
            return 0.0
        no_shows = len(self.get_no_shows())
        return (no_shows / len(self._all_meetings)) * 100.0

    def get_meeting_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for meeting in self._all_meetings:
            counts[meeting.meeting_type] = counts.get(meeting.meeting_type, 0) + 1
        return counts

    def get_todays_meetings(self) -> list[MeetingEvent]:
        today = datetime.now(UTC).date()
        return [
            m for m in self._all_meetings
            if m.timestamp.date() == today
        ]
