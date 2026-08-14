"""Opportunity scoring — re-exports Lead Quality Score (LQS)."""

from lead_quality import (
    OUTBOUND_THRESHOLD,
    PERFECT_THRESHOLD,
    SCORING_VERSION,
    LeadQualityScorer,
    annotate_payload,
    is_outbound_ready,
    is_perfect_lead,
)

__all__ = [
    "OUTBOUND_THRESHOLD",
    "PERFECT_THRESHOLD",
    "SCORING_VERSION",
    "LeadQualityScorer",
    "annotate_payload",
    "is_outbound_ready",
    "is_perfect_lead",
]
