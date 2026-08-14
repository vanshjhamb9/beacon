"""Live Opportunity Inbox — every new opportunity enters here.

NOT Revenue Ready immediately.
Every record contains: Company, Website, Buying Signal, Evidence, Connector,
Quality Score, Signal Age, Why Now, Revenue Potential, Created, Status.

Status defaults to NEW.
Founder actions: Approve, Reject, Archive, Spam, Competitor, Future Opportunity,
Watchlist, Duplicate, Merge, Delete, Assign.

Nothing becomes Revenue Ready without approval.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import OpportunityStage, InboxAction


class InboxRecord:
    """Single inbox record for an opportunity."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.company_name: str = data.get("company_name", "unknown")
        self.website: str = data.get("website", "unknown")
        self.buying_signal: str = data.get("buying_signal", "unknown")
        self.evidence: dict[str, Any] = data.get("evidence", {})
        self.connector: str = data.get("connector", "unknown")
        self.quality_score: int = data.get("quality_score", 0)
        self.signal_age_days: int = data.get("signal_age_days", 0)
        self.why_now: str = data.get("why_now", "unknown")
        self.revenue_potential: str = data.get("revenue_potential", "unknown")
        self.status: str = data.get("status", OpportunityStage.NEW.value)
        self.assigned_to: str = data.get("assigned_to", "unassigned")
        self.tags: list[str] = data.get("tags", [])
        self.notes: list[dict[str, Any]] = data.get("notes", [])
        self.created_at: datetime = data.get("created_at", datetime.now(timezone.utc))
        self.updated_at: datetime = data.get("updated_at", datetime.now(timezone.utc))
        self.stage_history: list[dict[str, Any]] = data.get("stage_history", [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "website": self.website,
            "buying_signal": self.buying_signal,
            "evidence": self.evidence,
            "connector": self.connector,
            "quality_score": self.quality_score,
            "signal_age_days": self.signal_age_days,
            "why_now": self.why_now,
            "revenue_potential": self.revenue_potential,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "stage_history": self.stage_history,
        }


class InboxEngine:
    """Live Opportunity Inbox engine."""

    def __init__(self):
        self._records: dict[str, InboxRecord] = {}
        self._history: list[dict[str, Any]] = []

    def add_opportunity(
        self,
        company_name: str,
        website: str,
        buying_signal: str,
        evidence: dict[str, Any],
        connector: str,
        quality_score: int,
        signal_age_days: int,
        why_now: str,
        revenue_potential: str = "unknown",
    ) -> InboxRecord:
        """Add new opportunity to inbox."""
        record = InboxRecord({
            "company_name": company_name,
            "website": website,
            "buying_signal": buying_signal,
            "evidence": evidence,
            "connector": connector,
            "quality_score": quality_score,
            "signal_age_days": signal_age_days,
            "why_now": why_now,
            "revenue_potential": revenue_potential,
            "status": OpportunityStage.NEW.value,
            "stage_history": [
                {
                    "stage": OpportunityStage.NEW.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "created",
                }
            ],
        })

        self._records[record.id] = record
        self._record_event(record.id, "created", OpportunityStage.NEW.value)
        return record

    def get_record(self, record_id: str) -> InboxRecord | None:
        """Get inbox record by ID."""
        return self._records.get(record_id)

    def get_all_records(self) -> list[InboxRecord]:
        """Get all inbox records."""
        return list(self._records.values())

    def get_records_by_status(self, status: str) -> list[InboxRecord]:
        """Get records by status."""
        return [r for r in self._records.values() if r.status == status]

    def get_records_by_connector(self, connector: str) -> list[InboxRecord]:
        """Get records by connector."""
        return [r for r in self._records.values() if r.connector == connector]

    def update_status(
        self,
        record_id: str,
        new_status: str,
        action: str = "manual",
        notes: str | None = None,
    ) -> InboxRecord | None:
        """Update opportunity status."""
        record = self._records.get(record_id)
        if not record:
            return None

        old_status = record.status
        record.status = new_status
        record.updated_at = datetime.now(timezone.utc)

        record.stage_history.append({
            "from": old_status,
            "to": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "notes": notes,
        })

        self._record_event(record_id, action, new_status)
        return record

    def approve(self, record_id: str, notes: str | None = None) -> InboxRecord | None:
        """Approve opportunity."""
        return self.update_status(record_id, OpportunityStage.APPROVED.value, "approve", notes)

    def reject(self, record_id: str, notes: str | None = None) -> InboxRecord | None:
        """Reject opportunity."""
        return self.update_status(record_id, OpportunityStage.ARCHIVED.value, "reject", notes)

    def archive(self, record_id: str, notes: str | None = None) -> InboxRecord | None:
        """Archive opportunity."""
        return self.update_status(record_id, OpportunityStage.ARCHIVED.value, "archive", notes)

    def mark_spam(self, record_id: str, notes: str | None = None) -> InboxRecord | None:
        """Mark as spam."""
        return self.update_status(record_id, OpportunityStage.SPAM.value, "spam", notes)

    def mark_not_icp(self, record_id: str, notes: str | None = None) -> InboxRecord | None:
        """Mark as not ICP."""
        return self.update_status(record_id, OpportunityStage.NOT_ICP.value, "not_icp", notes)

    def assign(self, record_id: str, assignee: str) -> InboxRecord | None:
        """Assign opportunity."""
        record = self._records.get(record_id)
        if not record:
            return None
        record.assigned_to = assignee
        record.updated_at = datetime.now(timezone.utc)
        return record

    def add_note(self, record_id: str, note: str, author: str = "founder") -> bool:
        """Add note to opportunity."""
        record = self._records.get(record_id)
        if not record:
            return False
        record.notes.append({
            "note": note,
            "author": author,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        record.updated_at = datetime.now(timezone.utc)
        return True

    def add_tag(self, record_id: str, tag: str) -> bool:
        """Add tag to opportunity."""
        record = self._records.get(record_id)
        if not record:
            return False
        if tag not in record.tags:
            record.tags.append(tag)
            record.updated_at = datetime.now(timezone.utc)
        return True

    def remove_tag(self, record_id: str, tag: str) -> bool:
        """Remove tag from opportunity."""
        record = self._records.get(record_id)
        if not record:
            return False
        if tag in record.tags:
            record.tags.remove(tag)
            record.updated_at = datetime.now(timezone.utc)
        return True

    def bulk_update_status(
        self,
        record_ids: list[str],
        new_status: str,
        action: str = "bulk",
    ) -> list[InboxRecord]:
        """Bulk update status for multiple records."""
        updated = []
        for record_id in record_ids:
            record = self.update_status(record_id, new_status, action)
            if record:
                updated.append(record)
        return updated

    def search(self, query: str) -> list[InboxRecord]:
        """Search inbox records by company name or tags."""
        query_lower = query.lower()
        results = []
        for record in self._records.values():
            if query_lower in record.company_name.lower():
                results.append(record)
            elif any(query_lower in tag.lower() for tag in record.tags):
                results.append(record)
        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get inbox statistics."""
        total = len(self._records)
        by_status = {}
        by_connector = {}
        total_quality = 0

        for record in self._records.values():
            by_status[record.status] = by_status.get(record.status, 0) + 1
            by_connector[record.connector] = by_connector.get(record.connector, 0) + 1
            total_quality += record.quality_score

        return {
            "total": total,
            "by_status": by_status,
            "by_connector": by_connector,
            "avg_quality_score": round(total_quality / total, 2) if total > 0 else 0,
            "new_today": self._count_new_today(),
        }

    def _count_new_today(self) -> int:
        """Count opportunities created today."""
        today = datetime.now(timezone.utc).date()
        count = 0
        for record in self._records.values():
            if record.created_at.date() == today:
                count += 1
        return count

    def _record_event(self, record_id: str, action: str, status: str):
        """Record event for audit trail."""
        self._history.append({
            "record_id": record_id,
            "action": action,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_history(self) -> list[dict[str, Any]]:
        """Get inbox history."""
        return list(self._history)
