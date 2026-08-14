"""LOVP v1 schemas — deterministic validation types.

Every field required. NULL not allowed. Unknown acceptable.
No guessing permitted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ARCHIVE = "archive"
    SPAM = "spam"
    DUPLICATE = "duplicate"
    COMPETITOR = "competitor"
    FUTURE_OPPORTUNITY = "future_opportunity"
    WATCHLIST = "watchlist"


class StalenessStatus(str, Enum):
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    ANCIENT = "ancient"


class SignalOrigin(str, Enum):
    CONNECTOR = "connector"
    MANUAL = "manual"
    REPLAY = "replay"


class OpportunityMetadata:
    """Every field required. NULL not allowed. Unknown acceptable."""

    def __init__(self, data: dict[str, Any]):
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.company_name: str = data.get("company_name", "unknown")
        self.website: str = data.get("website", "unknown")
        self.evidence_source: str = data.get("evidence_source", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.original_url: str = data.get("original_url", "unknown")
        self.original_timestamp: datetime = data.get("original_timestamp", datetime.now(timezone.utc))
        self.collection_timestamp: datetime = data.get("collection_timestamp", datetime.now(timezone.utc))
        self.buying_signal: str = data.get("buying_signal", "unknown")
        self.signal_age_days: int = data.get("signal_age_days", -1)
        self.signal_type: str = data.get("signal_type", "unknown")
        self.confidence: float = data.get("confidence", 0.0)
        self.quality_score: int = data.get("quality_score", 0)
        self.freshness: str = data.get("freshness", "unknown")
        self.icp_match: bool = data.get("icp_match", False)
        self.region_match: bool = data.get("region_match", False)
        self.industry_match: bool = data.get("industry_match", False)
        self.why_now: str = data.get("why_now", "unknown")
        self.why_beacon_accepted: str = data.get("why_beacon_accepted", "unknown")
        self.why_beacon_rejected: str = data.get("why_beacon_rejected", "unknown")
        self.root_cause: str = data.get("root_cause", "unknown")
        self.human_verdict: str = data.get("human_verdict", "unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "company_name": self.company_name,
            "website": self.website,
            "evidence_source": self.evidence_source,
            "connector": self.connector,
            "original_url": self.original_url,
            "original_timestamp": self.original_timestamp.isoformat() if isinstance(self.original_timestamp, datetime) else str(self.original_timestamp),
            "collection_timestamp": self.collection_timestamp.isoformat() if isinstance(self.collection_timestamp, datetime) else str(self.collection_timestamp),
            "buying_signal": self.buying_signal,
            "signal_age_days": self.signal_age_days,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "freshness": self.freshness,
            "icp_match": self.icp_match,
            "region_match": self.region_match,
            "industry_match": self.industry_match,
            "why_now": self.why_now,
            "why_beacon_accepted": self.why_beacon_accepted,
            "why_beacon_rejected": self.why_beacon_rejected,
            "root_cause": self.root_cause,
            "human_verdict": self.human_verdict,
        }


class TimelineEvent:
    def __init__(self, data: dict[str, Any]):
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))
        self.event_type: str = data.get("event_type", "unknown")
        self.description: str = data.get("description", "unknown")
        self.source: str = data.get("source", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.confidence: float = data.get("confidence", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "event_type": self.event_type,
            "description": self.description,
            "source": self.source,
            "connector": self.connector,
            "confidence": self.confidence,
        }


class ValidationOutcome:
    def __init__(self, data: dict[str, Any]):
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.decision: str = data.get("decision", "unknown")
        self.validator: str = data.get("validator", "system")
        self.reasons: list[str] = data.get("reasons", [])
        self.evidence: dict[str, Any] = data.get("evidence", {})
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "decision": self.decision,
            "validator": self.validator,
            "reasons": self.reasons,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
        }


class AuditEntry:
    def __init__(self, data: dict[str, Any]):
        self.opportunity_id: str = data.get("opportunity_id", "unknown")
        self.gate: str = data.get("gate", "unknown")
        self.decision: str = data.get("decision", "unknown")
        self.reasons: list[str] = data.get("reasons", [])
        self.evidence: dict[str, Any] = data.get("evidence", {})
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "gate": self.gate,
            "decision": self.decision,
            "reasons": self.reasons,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
        }
