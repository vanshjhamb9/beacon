"""Reply Tracker — tracks replies to outreach."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ReplyRecord:
    """Single reply record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.outreach_id: str = data.get("outreach_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.contact_email: str = data.get("contact_email", "unknown")
        self.sentiment: str = data.get("sentiment", "neutral")
        self.content_preview: str = data.get("content_preview", "")
        self.received_at: datetime = data.get("received_at", datetime.now(timezone.utc))
        self.contacted_at: datetime = data.get("contacted_at", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "outreach_id": self.outreach_id,
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "sentiment": self.sentiment,
            "content_preview": self.content_preview,
            "received_at": self.received_at.isoformat(),
            "contacted_at": self.contacted_at.isoformat(),
        }


class ReplyTracker:
    """Tracks all replies to outreach."""

    def __init__(self):
        self._records: dict[str, ReplyRecord] = {}
        self._by_opportunity: dict[str, list[str]] = {}

    def record_reply(
        self,
        opportunity_id: str,
        outreach_id: str,
        company_name: str,
        contact_email: str,
        sentiment: str = "neutral",
        content_preview: str = "",
    ) -> ReplyRecord:
        """Record a reply."""
        record = ReplyRecord({
            "opportunity_id": opportunity_id,
            "outreach_id": outreach_id,
            "company_name": company_name,
            "contact_email": contact_email,
            "sentiment": sentiment,
            "content_preview": content_preview,
        })

        self._records[record.id] = record

        if opportunity_id not in self._by_opportunity:
            self._by_opportunity[opportunity_id] = []
        self._by_opportunity[opportunity_id].append(record.id)

        return record

    def get_record(self, record_id: str) -> ReplyRecord | None:
        """Get reply record."""
        return self._records.get(record_id)

    def get_records_for_opportunity(self, opportunity_id: str) -> list[ReplyRecord]:
        """Get all replies for opportunity."""
        record_ids = self._by_opportunity.get(opportunity_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def get_all_records(self) -> list[ReplyRecord]:
        """Get all reply records."""
        return list(self._records.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get reply statistics."""
        total = len(self._records)
        positive = sum(1 for r in self._records.values() if r.sentiment == "positive")
        negative = sum(1 for r in self._records.values() if r.sentiment == "negative")
        neutral = sum(1 for r in self._records.values() if r.sentiment == "neutral")

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_rate": round(positive / max(total, 1), 3),
        }
