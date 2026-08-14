"""Outreach Tracker — tracks outreach activities and responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class OutreachRecord:
    """Single outreach record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.contact_email: str = data.get("contact_email", "unknown")
        self.outreach_type: str = data.get("outreach_type", "email")
        self.subject: str = data.get("subject", "")
        self.status: str = data.get("status", "sent")
        self.sent_at: datetime = data.get("sent_at", datetime.now(timezone.utc))
        self.opened_at: datetime | None = data.get("opened_at")
        self.clicked_at: datetime | None = data.get("clicked_at")
        self.replied_at: datetime | None = data.get("replied_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "outreach_type": self.outreach_type,
            "subject": self.subject,
            "status": self.status,
            "sent_at": self.sent_at.isoformat(),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "replied_at": self.replied_at.isoformat() if self.replied_at else None,
        }


class OutreachTracker:
    """Tracks all outreach activities."""

    def __init__(self):
        self._records: dict[str, OutreachRecord] = {}
        self._by_opportunity: dict[str, list[str]] = {}

    def record_outreach(
        self,
        opportunity_id: str,
        company_name: str,
        contact_email: str,
        outreach_type: str = "email",
        subject: str = "",
    ) -> OutreachRecord:
        """Record an outreach."""
        record = OutreachRecord({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "contact_email": contact_email,
            "outreach_type": outreach_type,
            "subject": subject,
        })

        self._records[record.id] = record

        if opportunity_id not in self._by_opportunity:
            self._by_opportunity[opportunity_id] = []
        self._by_opportunity[opportunity_id].append(record.id)

        return record

    def mark_opened(self, record_id: str) -> bool:
        """Mark outreach as opened."""
        record = self._records.get(record_id)
        if record:
            record.opened_at = datetime.now(timezone.utc)
            record.status = "opened"
            return True
        return False

    def mark_clicked(self, record_id: str) -> bool:
        """Mark outreach as clicked."""
        record = self._records.get(record_id)
        if record:
            record.clicked_at = datetime.now(timezone.utc)
            record.status = "clicked"
            return True
        return False

    def mark_replied(self, record_id: str) -> bool:
        """Mark outreach as replied."""
        record = self._records.get(record_id)
        if record:
            record.replied_at = datetime.now(timezone.utc)
            record.status = "replied"
            return True
        return False

    def get_record(self, record_id: str) -> OutreachRecord | None:
        """Get outreach record."""
        return self._records.get(record_id)

    def get_records_for_opportunity(self, opportunity_id: str) -> list[OutreachRecord]:
        """Get all outreach records for opportunity."""
        record_ids = self._by_opportunity.get(opportunity_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def get_all_records(self) -> list[OutreachRecord]:
        """Get all outreach records."""
        return list(self._records.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get outreach statistics."""
        total = len(self._records)
        sent = sum(1 for r in self._records.values() if r.status == "sent")
        opened = sum(1 for r in self._records.values() if r.opened_at)
        clicked = sum(1 for r in self._records.values() if r.clicked_at)
        replied = sum(1 for r in self._records.values() if r.replied_at)

        return {
            "total": total,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "open_rate": round(opened / max(total, 1), 3),
            "click_rate": round(clicked / max(total, 1), 3),
            "reply_rate": round(replied / max(total, 1), 3),
        }
