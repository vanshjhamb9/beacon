"""Revenue Tracker — tracks revenue and financial metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class RevenueRecord:
    """Single revenue record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.amount: float = data.get("amount", 0.0)
        self.revenue_type: str = data.get("revenue_type", "subscription")
        self.status: str = data.get("status", "pending")
        self.closed_at: datetime | None = data.get("closed_at")
        self.notes: str = data.get("notes", "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "amount": self.amount,
            "revenue_type": self.revenue_type,
            "status": self.status,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "notes": self.notes,
        }


class RevenueTracker:
    """Tracks all revenue."""

    def __init__(self):
        self._records: dict[str, RevenueRecord] = {}
        self._by_opportunity: dict[str, list[str]] = {}

    def record_revenue(
        self,
        opportunity_id: str,
        company_name: str,
        amount: float,
        revenue_type: str = "subscription",
    ) -> RevenueRecord:
        """Record revenue."""
        record = RevenueRecord({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "amount": amount,
            "revenue_type": revenue_type,
        })

        self._records[record.id] = record

        if opportunity_id not in self._by_opportunity:
            self._by_opportunity[opportunity_id] = []
        self._by_opportunity[opportunity_id].append(record.id)

        return record

    def mark_closed(self, record_id: str, notes: str = "") -> bool:
        """Mark revenue as closed."""
        record = self._records.get(record_id)
        if record:
            record.closed_at = datetime.now(timezone.utc)
            record.status = "closed"
            record.notes = notes
            return True
        return False

    def get_record(self, record_id: str) -> RevenueRecord | None:
        """Get revenue record."""
        return self._records.get(record_id)

    def get_records_for_opportunity(self, opportunity_id: str) -> list[RevenueRecord]:
        """Get all revenue for opportunity."""
        record_ids = self._by_opportunity.get(opportunity_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def get_all_records(self) -> list[RevenueRecord]:
        """Get all revenue records."""
        return list(self._records.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get revenue statistics."""
        total = len(self._records)
        closed = sum(1 for r in self._records.values() if r.status == "closed")
        total_amount = sum(r.amount for r in self._records.values())
        closed_amount = sum(r.amount for r in self._records.values() if r.status == "closed")
        avg_deal_size = closed_amount / max(closed, 1)

        by_type: dict[str, float] = {}
        for r in self._records.values():
            by_type[r.revenue_type] = by_type.get(r.revenue_type, 0) + r.amount

        return {
            "total": total,
            "closed": closed,
            "total_amount": total_amount,
            "closed_amount": closed_amount,
            "avg_deal_size": round(avg_deal_size, 2),
            "by_type": by_type,
        }
