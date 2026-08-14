"""Meeting Tracker — tracks meetings and outcomes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class MeetingRecord:
    """Single meeting record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.contact_email: str = data.get("contact_email", "unknown")
        self.meeting_type: str = data.get("meeting_type", "discovery")
        self.status: str = data.get("status", "scheduled")
        self.scheduled_at: datetime = data.get("scheduled_at", datetime.now(timezone.utc))
        self.completed_at: datetime | None = data.get("completed_at")
        self.outcome: str | None = data.get("outcome")
        self.notes: str = data.get("notes", "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "meeting_type": self.meeting_type,
            "status": self.status,
            "scheduled_at": self.scheduled_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "outcome": self.outcome,
            "notes": self.notes,
        }


class MeetingTracker:
    """Tracks all meetings."""

    def __init__(self):
        self._records: dict[str, MeetingRecord] = {}
        self._by_opportunity: dict[str, list[str]] = {}

    def record_meeting(
        self,
        opportunity_id: str,
        company_name: str,
        contact_email: str,
        meeting_type: str = "discovery",
        scheduled_at: datetime | None = None,
    ) -> MeetingRecord:
        """Record a meeting."""
        record = MeetingRecord({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "contact_email": contact_email,
            "meeting_type": meeting_type,
            "scheduled_at": scheduled_at or datetime.now(timezone.utc),
        })

        self._records[record.id] = record

        if opportunity_id not in self._by_opportunity:
            self._by_opportunity[opportunity_id] = []
        self._by_opportunity[opportunity_id].append(record.id)

        return record

    def mark_completed(self, record_id: str, outcome: str = "completed", notes: str = "") -> bool:
        """Mark meeting as completed."""
        record = self._records.get(record_id)
        if record:
            record.completed_at = datetime.now(timezone.utc)
            record.status = "completed"
            record.outcome = outcome
            record.notes = notes
            return True
        return False

    def mark_no_show(self, record_id: str) -> bool:
        """Mark meeting as no-show."""
        record = self._records.get(record_id)
        if record:
            record.status = "no_show"
            record.outcome = "no_show"
            return True
        return False

    def mark_rescheduled(self, record_id: str) -> bool:
        """Mark meeting as rescheduled."""
        record = self._records.get(record_id)
        if record:
            record.status = "rescheduled"
            return True
        return False

    def get_record(self, record_id: str) -> MeetingRecord | None:
        """Get meeting record."""
        return self._records.get(record_id)

    def get_records_for_opportunity(self, opportunity_id: str) -> list[MeetingRecord]:
        """Get all meetings for opportunity."""
        record_ids = self._by_opportunity.get(opportunity_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def get_all_records(self) -> list[MeetingRecord]:
        """Get all meeting records."""
        return list(self._records.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get meeting statistics."""
        total = len(self._records)
        completed = sum(1 for r in self._records.values() if r.status == "completed")
        no_show = sum(1 for r in self._records.values() if r.status == "no_show")
        scheduled = sum(1 for r in self._records.values() if r.status == "scheduled")

        return {
            "total": total,
            "completed": completed,
            "no_show": no_show,
            "scheduled": scheduled,
            "completion_rate": round(completed / max(total, 1), 3),
            "no_show_rate": round(no_show / max(total, 1), 3),
        }
