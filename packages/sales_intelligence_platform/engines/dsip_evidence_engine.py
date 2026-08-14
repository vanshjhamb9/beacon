"""DSIP: Evidence Engine.

Every extracted field must include evidence.
Evidence is immutable. Never lose evidence.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    """Immutable evidence for an extracted field."""
    field_name: str
    field_value: str
    source_id: str
    connector_type: str
    evidence_url: str = ""
    extraction_method: str = "unknown"  # html_parse, api, regex, structured_data
    extraction_version: str = "1.0"
    confidence: float = 0.0
    is_verified: bool = False
    verification_method: str = ""
    first_extracted: datetime = field(default_factory=datetime.utcnow)
    last_verified: datetime | None = None
    evidence_hash: str = ""
    conflicts_with: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.evidence_hash:
            self.evidence_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of evidence."""
        content = f"{self.field_name}:{self.field_value}:{self.source_id}:{self.first_extracted.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()


class EvidenceEngine:
    """Manages immutable evidence for every extracted field.

    Every field extracted by a connector gets an Evidence record.
    Evidence is never modified after creation — only appended.

    Usage:
        engine = EvidenceEngine()
        evidence = engine.create_evidence(
            field_name="website",
            field_value="https://mamaearth.in",
            source_id="google_search",
            ...
        )
        all_evidence = engine.get_company_evidence(company_id)
    """

    def __init__(self):
        self._evidence_store: dict[str, list[Evidence]] = {}  # company_id -> [Evidence]
        self._evidence_index: dict[str, Evidence] = {}  # evidence_hash -> Evidence

    def create_evidence(
        self,
        company_id: str,
        field_name: str,
        field_value: str,
        source_id: str,
        connector_type: str,
        evidence_url: str = "",
        extraction_method: str = "unknown",
        confidence: float = 0.5,
        **kwargs,
    ) -> Evidence:
        """Create a new evidence record."""
        evidence = Evidence(
            field_name=field_name,
            field_value=field_value,
            source_id=source_id,
            connector_type=connector_type,
            evidence_url=evidence_url,
            extraction_method=extraction_method,
            confidence=confidence,
            **kwargs,
        )

        # Store
        self._evidence_store.setdefault(company_id, []).append(evidence)
        self._evidence_index[evidence.evidence_hash] = evidence

        logger.debug(
            f"Evidence created: {field_name}={field_value[:50]} "
            f"(source={source_id}, confidence={confidence:.2f})"
        )

        return evidence

    def create_batch_evidence(
        self,
        company_id: str,
        fields: list[dict],
        source_id: str,
        connector_type: str,
    ) -> list[Evidence]:
        """Create evidence for multiple fields at once."""
        evidence_list = []
        for field_data in fields:
            evidence = self.create_evidence(
                company_id=company_id,
                field_name=field_data.get("field_name", ""),
                field_value=field_data.get("field_value", ""),
                source_id=source_id,
                connector_type=connector_type,
                evidence_url=field_data.get("evidence_url", ""),
                extraction_method=field_data.get("extraction_method", "unknown"),
                confidence=field_data.get("confidence", 0.5),
            )
            evidence_list.append(evidence)
        return evidence_list

    def get_company_evidence(
        self,
        company_id: str,
        field_name: str = None,
        source_id: str = None,
    ) -> list[Evidence]:
        """Get evidence for a company, optionally filtered."""
        evidence_list = self._evidence_store.get(company_id, [])

        if field_name:
            evidence_list = [e for e in evidence_list if e.field_name == field_name]

        if source_id:
            evidence_list = [e for e in evidence_list if e.source_id == source_id]

        return evidence_list

    def get_field_value(
        self,
        company_id: str,
        field_name: str,
        strategy: str = "highest_confidence",
    ) -> dict | None:
        """Get the best value for a field based on strategy.

        Strategies:
        - highest_confidence: Return value with highest confidence
        - most_recent: Return most recently extracted value
        - most_sources: Return value confirmed by most sources
        """
        evidence_list = self.get_company_evidence(company_id, field_name)
        if not evidence_list:
            return None

        if strategy == "highest_confidence":
            best = max(evidence_list, key=lambda e: e.confidence)
        elif strategy == "most_recent":
            best = max(evidence_list, key=lambda e: e.first_extracted)
        elif strategy == "most_recent":
            # Group by value, count sources
            value_counts = {}
            for e in evidence_list:
                value_counts.setdefault(e.field_value, set()).add(e.source_id)
            best_value = max(value_counts.items(), key=lambda x: len(x[1]))[0]
            best = next(e for e in evidence_list if e.field_value == best_value)
        else:
            best = max(evidence_list, key=lambda e: e.confidence)

        return {
            "value": best.field_value,
            "confidence": best.confidence,
            "source": best.source_id,
            "evidence_count": len(evidence_list),
            "first_extracted": best.first_extracted.isoformat(),
        }

    def detect_conflicts(self, company_id: str) -> list[dict]:
        """Detect conflicting evidence for a field."""
        evidence_list = self.get_company_evidence(company_id)
        conflicts = []

        # Group by field name
        by_field = {}
        for e in evidence_list:
            by_field.setdefault(e.field_name, []).append(e)

        for field_name, field_evidence in by_field.items():
            # Check for different values
            values = set(e.field_value for e in field_evidence)
            if len(values) > 1:
                conflicts.append({
                    "field": field_name,
                    "values": [
                        {
                            "value": e.field_value,
                            "source": e.source_id,
                            "confidence": e.confidence,
                        }
                        for e in field_evidence
                    ],
                    "conflict_count": len(values),
                })

        return conflicts

    def get_evidence_quality(self, company_id: str) -> dict:
        """Assess overall evidence quality for a company."""
        evidence_list = self.get_company_evidence(company_id)
        if not evidence_list:
            return {"score": 0, "field_count": 0, "source_count": 0}

        # Metrics
        fields_covered = set(e.field_name for e in evidence_list)
        sources_used = set(e.source_id for e in evidence_list)
        avg_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
        verified_count = sum(1 for e in evidence_list if e.is_verified)

        # Score
        field_score = min(100, len(fields_covered) * 10)  # 10 points per field
        source_score = min(100, len(sources_used) * 20)  # 20 points per source
        confidence_score = avg_confidence * 100
        verification_score = (verified_count / len(evidence_list)) * 100

        overall_score = (
            field_score * 0.3 +
            source_score * 0.3 +
            confidence_score * 0.25 +
            verification_score * 0.15
        )

        return {
            "score": overall_score,
            "field_count": len(fields_covered),
            "source_count": len(sources_used),
            "avg_confidence": avg_confidence,
            "verified_count": verified_count,
            "total_evidence": len(evidence_list),
            "fields": list(fields_covered),
        }

    def get_evidence_stats(self) -> dict:
        """Get overall evidence statistics."""
        total_evidence = sum(len(v) for v in self._evidence_store.values())
        total_companies = len(self._evidence_store)

        return {
            "total_evidence": total_evidence,
            "total_companies": total_companies,
            "avg_evidence_per_company": total_evidence / total_companies if total_companies > 0 else 0,
        }
