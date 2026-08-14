"""Rejection Explorer — analyzes rejections with evidence."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from . import REJECTION_CATEGORIES


class RejectionRecord:
    """Single rejection record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.rejection_category: str = data.get("rejection_category", "unknown")
        self.rejection_reason: str = data.get("rejection_reason", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.signal_age_days: int = data.get("signal_age_days", 0)
        self.quality_score: int = data.get("quality_score", 0)
        self.evidence: dict[str, Any] = data.get("evidence", {})
        self.rejected_at: datetime = data.get("rejected_at", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "rejection_category": self.rejection_category,
            "rejection_reason": self.rejection_reason,
            "connector": self.connector,
            "signal_age_days": self.signal_age_days,
            "quality_score": self.quality_score,
            "evidence": self.evidence,
            "rejected_at": self.rejected_at.isoformat(),
        }


class RejectionExplorer:
    """Analyzes rejections with evidence."""

    def __init__(self):
        self._records: list[RejectionRecord] = []

    def add_rejection(
        self,
        opportunity_id: str,
        company_name: str,
        rejection_category: str,
        rejection_reason: str,
        connector: str,
        signal_age_days: int,
        quality_score: int,
        evidence: dict[str, Any] | None = None,
    ) -> RejectionRecord:
        """Add rejection record."""
        record = RejectionRecord({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "rejection_category": rejection_category,
            "rejection_reason": rejection_reason,
            "connector": connector,
            "signal_age_days": signal_age_days,
            "quality_score": quality_score,
            "evidence": evidence or {},
        })

        self._records.append(record)
        return record

    def get_all_rejections(self) -> list[RejectionRecord]:
        """Get all rejection records."""
        return list(self._records)

    def get_by_category(self, category: str) -> list[RejectionRecord]:
        """Get rejections by category."""
        return [r for r in self._records if r.rejection_category == category]

    def get_by_connector(self, connector: str) -> list[RejectionRecord]:
        """Get rejections by connector."""
        return [r for r in self._records if r.connector == connector]

    def get_statistics(self) -> dict[str, Any]:
        """Get rejection statistics."""
        total = len(self._records)
        by_category = {}
        by_connector = {}

        for record in self._records:
            by_category[record.rejection_category] = by_category.get(record.rejection_category, 0) + 1
            by_connector[record.connector] = by_connector.get(record.connector, 0) + 1

        # Sort by count
        top_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_rejections": total,
            "by_category": by_category,
            "by_connector": by_connector,
            "top_categories": [{"category": c, "count": n} for c, n in top_categories[:10]],
        }

    def get_rejection_tree(self) -> dict[str, Any]:
        """Get rejection tree for founder debug."""
        stats = self.get_statistics()
        total = stats["total_rejections"]

        tree = {"total_rejected": total}
        for category, count in stats["by_category"].items():
            description = REJECTION_CATEGORIES.get(category, category)
            tree[category] = {
                "count": count,
                "percentage": round(count / max(total, 1) * 100, 1),
                "description": description,
            }

        return tree
