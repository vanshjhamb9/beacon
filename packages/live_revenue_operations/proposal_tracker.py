"""Proposal Tracker — tracks proposals and their status."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ProposalRecord:
    """Single proposal record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.proposal_type: str = data.get("proposal_type", "standard")
        self.amount: float = data.get("amount", 0.0)
        self.status: str = data.get("status", "draft")
        self.sent_at: datetime | None = data.get("sent_at")
        self.viewed_at: datetime | None = data.get("viewed_at")
        self.accepted_at: datetime | None = data.get("accepted_at")
        self.declined_at: datetime | None = data.get("declined_at")
        self.notes: str = data.get("notes", "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "proposal_type": self.proposal_type,
            "amount": self.amount,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "declined_at": self.declined_at.isoformat() if self.declined_at else None,
            "notes": self.notes,
        }


class ProposalTracker:
    """Tracks all proposals."""

    def __init__(self):
        self._records: dict[str, ProposalRecord] = {}
        self._by_opportunity: dict[str, list[str]] = {}

    def record_proposal(
        self,
        opportunity_id: str,
        company_name: str,
        proposal_type: str = "standard",
        amount: float = 0.0,
    ) -> ProposalRecord:
        """Record a proposal."""
        record = ProposalRecord({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "proposal_type": proposal_type,
            "amount": amount,
        })

        self._records[record.id] = record

        if opportunity_id not in self._by_opportunity:
            self._by_opportunity[opportunity_id] = []
        self._by_opportunity[opportunity_id].append(record.id)

        return record

    def mark_sent(self, record_id: str) -> bool:
        """Mark proposal as sent."""
        record = self._records.get(record_id)
        if record:
            record.sent_at = datetime.now(timezone.utc)
            record.status = "sent"
            return True
        return False

    def mark_viewed(self, record_id: str) -> bool:
        """Mark proposal as viewed."""
        record = self._records.get(record_id)
        if record:
            record.viewed_at = datetime.now(timezone.utc)
            record.status = "viewed"
            return True
        return False

    def mark_accepted(self, record_id: str) -> bool:
        """Mark proposal as accepted."""
        record = self._records.get(record_id)
        if record:
            record.accepted_at = datetime.now(timezone.utc)
            record.status = "accepted"
            return True
        return False

    def mark_declined(self, record_id: str, notes: str = "") -> bool:
        """Mark proposal as declined."""
        record = self._records.get(record_id)
        if record:
            record.declined_at = datetime.now(timezone.utc)
            record.status = "declined"
            record.notes = notes
            return True
        return False

    def get_record(self, record_id: str) -> ProposalRecord | None:
        """Get proposal record."""
        return self._records.get(record_id)

    def get_records_for_opportunity(self, opportunity_id: str) -> list[ProposalRecord]:
        """Get all proposals for opportunity."""
        record_ids = self._by_opportunity.get(opportunity_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def get_all_records(self) -> list[ProposalRecord]:
        """Get all proposal records."""
        return list(self._records.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get proposal statistics."""
        total = len(self._records)
        sent = sum(1 for r in self._records.values() if r.status == "sent")
        viewed = sum(1 for r in self._records.values() if r.viewed_at)
        accepted = sum(1 for r in self._records.values() if r.accepted_at)
        declined = sum(1 for r in self._records.values() if r.declined_at)
        total_amount = sum(r.amount for r in self._records.values())
        accepted_amount = sum(r.amount for r in self._records.values() if r.accepted_at)

        return {
            "total": total,
            "sent": sent,
            "viewed": viewed,
            "accepted": accepted,
            "declined": declined,
            "total_amount": total_amount,
            "accepted_amount": accepted_amount,
            "acceptance_rate": round(accepted / max(total, 1), 3),
        }
