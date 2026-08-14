"""Evidence Explorer — makes every opportunity explainable."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class EvidenceRecord:
    """Single evidence record."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.website: str = data.get("website", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.evidence_url: str = data.get("evidence_url", "unknown")
        self.evidence_snapshot: str = data.get("evidence_snapshot", "")
        self.published_at: datetime | None = data.get("published_at")
        self.collected_at: datetime = data.get("collected_at", datetime.now(timezone.utc))
        self.buying_signal: str = data.get("buying_signal", "unknown")
        self.quality_score: int = data.get("quality_score", 0)
        self.validation_decision: str = data.get("validation_decision", "unknown")
        self.revenue_ready_decision: str = data.get("revenue_ready_decision", "unknown")
        self.timeline: list[dict[str, Any]] = data.get("timeline", [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "website": self.website,
            "connector": self.connector,
            "evidence_url": self.evidence_url,
            "evidence_snapshot": self.evidence_snapshot,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "collected_at": self.collected_at.isoformat(),
            "buying_signal": self.buying_signal,
            "quality_score": self.quality_score,
            "validation_decision": self.validation_decision,
            "revenue_ready_decision": self.revenue_ready_decision,
            "timeline": self.timeline,
        }


class EvidenceExplorer:
    """Makes every opportunity explainable."""

    def __init__(self):
        self._records: dict[str, EvidenceRecord] = {}

    def add_evidence(
        self,
        opportunity_id: str,
        company_name: str,
        website: str,
        connector: str,
        evidence_url: str,
        buying_signal: str,
        quality_score: int,
        validation_decision: str,
        revenue_ready_decision: str,
        published_at: datetime | None = None,
        evidence_snapshot: str = "",
    ) -> EvidenceRecord:
        """Add evidence record."""
        record = EvidenceRecord({
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "website": website,
            "connector": connector,
            "evidence_url": evidence_url,
            "buying_signal": buying_signal,
            "quality_score": quality_score,
            "validation_decision": validation_decision,
            "revenue_ready_decision": revenue_ready_decision,
            "published_at": published_at,
            "evidence_snapshot": evidence_snapshot,
        })

        self._records[opportunity_id] = record
        return record

    def get_evidence(self, opportunity_id: str) -> EvidenceRecord | None:
        """Get evidence for opportunity."""
        return self._records.get(opportunity_id)

    def get_all_evidence(self) -> list[EvidenceRecord]:
        """Get all evidence records."""
        return list(self._records.values())

    def search_by_company(self, company_name: str) -> list[EvidenceRecord]:
        """Search evidence by company name."""
        return [
            r for r in self._records.values()
            if company_name.lower() in r.company_name.lower()
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get evidence statistics."""
        total = len(self._records)
        by_connector = {}
        by_validation = {}

        for record in self._records.values():
            by_connector[record.connector] = by_connector.get(record.connector, 0) + 1
            by_validation[record.validation_decision] = by_validation.get(record.validation_decision, 0) + 1

        return {
            "total_records": total,
            "by_connector": by_connector,
            "by_validation": by_validation,
        }
