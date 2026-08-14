"""Core validation engine — determines if opportunity deserves pipeline entry.

Every opportunity goes through this engine before reaching Opportunity Intelligence.

Architecture:
    Collectors → Connector Platform → DQE → VALIDATOR → Opportunity Intelligence

Rules:
    - No NULLs allowed. Unknown is acceptable.
    - No guessing permitted.
    - Every decision must have evidence.
    - Every decision must be auditable.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from .v1_schemas import (
    OpportunityMetadata,
    TimelineEvent,
    ValidationOutcome,
    ReviewDecision,
    StalenessStatus,
)


class OpportunityValidator:
    """Deterministic validator — proves every company deserves pipeline entry."""

    # ICP thresholds
    MIN_QUALITY_SCORE = 75
    MAX_SIGNAL_AGE_DAYS = 120
    MIN_CONFIDENCE = 0.3
    MIN_TIMELINE_EVENTS = 1

    # Staleness thresholds
    FRESH_DAYS = 30
    AGING_DAYS = 90
    STALE_DAYS = 120

    # Known non-buying signals
    NOT_BUYING_SIGNALS = {
        "Blog posts",
        "Marketing articles",
        "Random tweets",
        "Motivational posts",
        "Old Product Hunt launches",
        "Conference attendance",
        "Podcast appearances",
        "Social media activity",
        "Press releases",
        "Case studies",
        "Whitepapers",
        "Webinars",
    }

    # Known AI/LLM companies (reject)
    AI_COMPANY_KEYWORDS = {
        "gpt", "llm", "openai", "anthropic", "claude", "chatgpt",
        "ai writing", "ai assistant", "ai generator", "artificial intelligence",
        "machine learning", "deep learning", "neural network", "large language model",
    }

    def validate(self, metadata: OpportunityMetadata) -> ValidationOutcome:
        """Run full validation pipeline. Returns deterministic outcome."""
        reasons: list[str] = []
        evidence: dict[str, Any] = {}
        decision = ReviewDecision.APPROVE

        # Gate 1: Company Validation
        if not self._validate_company(metadata):
            reasons.append("Company validation failed")
            evidence["company_validation"] = "failed"
            decision = ReviewDecision.REJECT

        # Gate 2: Signal Integrity
        if not self._validate_signal(metadata):
            reasons.append("Signal integrity check failed")
            evidence["signal_integrity"] = "failed"
            decision = ReviewDecision.REJECT

        # Gate 3: Website Check
        if not self._validate_website(metadata):
            reasons.append("Website validation failed")
            evidence["website_validation"] = "failed"
            decision = ReviewDecision.REJECT

        # Gate 4: AI Company Filter
        if self._is_ai_company(metadata):
            reasons.append("AI/LLM company detected")
            evidence["ai_filter"] = "rejected"
            decision = ReviewDecision.REJECT

        # Gate 5: Staleness Check
        staleness = self._check_staleness(metadata)
        evidence["staleness"] = staleness.value
        if staleness == StalenessStatus.ANCIENT:
            reasons.append(f"Signal too old: {metadata.signal_age_days} days")
            decision = ReviewDecision.REJECT

        # Gate 6: Buying Signal Validity
        if metadata.buying_signal in self.NOT_BUYING_SIGNALS:
            reasons.append(f"Invalid buying signal: {metadata.buying_signal}")
            evidence["buying_signal_validity"] = "not_valid"
            decision = ReviewDecision.REJECT

        # Gate 7: Quality Score Threshold
        if metadata.quality_score < self.MIN_QUALITY_SCORE:
            reasons.append(f"Quality score {metadata.quality_score} below threshold {self.MIN_QUALITY_SCORE}")
            evidence["quality_score"] = metadata.quality_score
            decision = ReviewDecision.REJECT

        # Gate 8: Confidence Threshold
        if metadata.confidence < self.MIN_CONFIDENCE:
            reasons.append(f"Confidence {metadata.confidence} below threshold {self.MIN_CONFIDENCE}")
            evidence["confidence"] = metadata.confidence
            decision = ReviewDecision.REJECT

        # Gate 9: ICP Match
        if not metadata.icp_match:
            reasons.append("No ICP match")
            evidence["icp_match"] = False

        # Gate 10: Region Match
        if not metadata.region_match:
            reasons.append("No region match")
            evidence["region_match"] = False

        # Gate 11: Industry Match
        if not metadata.industry_match:
            reasons.append("No industry match")
            evidence["industry_match"] = False

        # Gate 12: Timeline Completeness
        if not self._validate_timeline(metadata):
            reasons.append("No timeline events")
            evidence["timeline"] = "empty"

        # Gate 13: Duplicate/Competitor Detection
        if self._is_competitor(metadata):
            reasons.append("Competitor detected")
            evidence["competitor_filter"] = "rejected"
            decision = ReviewDecision.COMPETITOR

        if self._is_duplicate(metadata):
            reasons.append("Duplicate detected")
            evidence["duplicate_filter"] = "rejected"
            decision = ReviewDecision.DUPLICATE

        # Build why_beacon_accepted/rejected
        if decision == ReviewDecision.APPROVE:
            why_accepted = self._build_acceptance_reason(metadata, evidence)
            metadata.why_beacon_accepted = why_accepted
            metadata.why_beacon_rejected = "N/A"
        else:
            metadata.why_beacon_rejected = "; ".join(reasons) if reasons else "Unknown rejection"
            metadata.why_beacon_accepted = "N/A"

        metadata.root_cause = self._determine_root_cause(decision, reasons)

        return ValidationOutcome(
            data={
                "opportunity_id": metadata.opportunity_id,
                "decision": decision.value,
                "validator": "deterministic_v1",
                "reasons": reasons,
                "evidence": evidence,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    def _validate_company(self, m: OpportunityMetadata) -> bool:
        if m.company_name in ("unknown", "", None):
            return False
        if len(m.company_name) < 2:
            return False
        return True

    def _validate_signal(self, m: OpportunityMetadata) -> bool:
        if m.buying_signal in ("unknown", "", None):
            return False
        if m.signal_type in ("unknown", "", None):
            return False
        if m.original_timestamp is None:
            return False
        return True

    def _validate_website(self, m: OpportunityMetadata) -> bool:
        if m.website in ("unknown", "", None):
            return False
        if not m.website.startswith(("http://", "https://")):
            return False
        if "parked" in m.website.lower():
            return False
        return True

    def _is_ai_company(self, m: OpportunityMetadata) -> bool:
        name_lower = m.company_name.lower()
        website_lower = m.website.lower()
        for keyword in self.AI_COMPANY_KEYWORDS:
            if keyword in name_lower or keyword in website_lower:
                return True
        return False

    def _check_staleness(self, m: OpportunityMetadata) -> StalenessStatus:
        if m.signal_age_days <= self.FRESH_DAYS:
            return StalenessStatus.FRESH
        elif m.signal_age_days <= self.AGING_DAYS:
            return StalenessStatus.AGING
        elif m.signal_age_days <= self.STALE_DAYS:
            return StalenessStatus.STALE
        else:
            return StalenessStatus.ANCIENT

    def _validate_timeline(self, m: OpportunityMetadata) -> bool:
        return True  # Timeline validated separately in timeline_builder

    def _is_competitor(self, m: OpportunityMetadata) -> bool:
        competitors = {"salesforce", "hubspot", "zoho", "pipedrive"}
        return m.company_name.lower() in competitors

    def _is_duplicate(self, m: OpportunityMetadata) -> bool:
        return False  # Duplicate check handled by duplicate_engine

    def _build_acceptance_reason(self, m: OpportunityMetadata, evidence: dict) -> str:
        parts = []
        parts.append(f"Signal: {m.buying_signal}")
        parts.append(f"Freshness: {m.freshness}")
        parts.append(f"Quality: {m.quality_score}/100")
        parts.append(f"ICP: {'match' if m.icp_match else 'no match'}")
        return "; ".join(parts)

    def _determine_root_cause(self, decision: ReviewDecision, reasons: list[str]) -> str:
        if decision == ReviewDecision.APPROVE:
            return "passes_all_gates"
        if not reasons:
            return "unknown"
        reason_lower = reasons[0].lower()
        if "no buying signal" in reason_lower or "invalid buying signal" in reason_lower:
            return "no_buying_signal"
        if "signal too old" in reason_lower:
            return "stale_signal"
        if "ai company" in reason_lower:
            return "ai_company"
        if "quality score" in reason_lower:
            return "low_quality_score"
        if "website" in reason_lower:
            return "no_website"
        if "duplicate" in reason_lower:
            return "duplicate"
        if "competitor" in reason_lower:
            return "competitor"
        if "no icp match" in reason_lower:
            return "no_icp_match"
        return "other"
