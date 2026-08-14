"""Confidence Engine - Calculate overall confidence in the account."""

from __future__ import annotations

from packages.sales_intelligence_platform.models import Account


def calculate_confidence(account: Account) -> float:
    """Calculate overall confidence score for the account.

    Returns a value between 0.0 and 100.0.
    """
    if not account.evidence_records:
        return 0.0

    # Average confidence of all evidence
    total_conf = sum(r.confidence for r in account.evidence_records)
    avg_conf = total_conf / len(account.evidence_records)

    # Bonus for verification
    verified_count = sum(
        1 for r in account.evidence_records
        if r.verification_status in ("VERIFIED", "LIKELY")
    )
    verification_bonus = min(20.0, verified_count * 3.0)

    # Bonus for multiple sources
    sources = set(r.source for r in account.evidence_records)
    source_bonus = min(15.0, len(sources) * 5.0)

    confidence = min(100.0, avg_conf * 100 + verification_bonus + source_bonus)

    # Add confidence to evidence records
    for r in account.evidence_records:
        r.confidence = min(1.0, r.confidence + (verification_bonus / 100.0))

    return round(confidence, 1)
