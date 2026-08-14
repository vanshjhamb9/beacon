"""Account Health Engine - Calculate account completeness and readiness."""

from __future__ import annotations

from packages.sales_intelligence_platform.models import Account, AccountHealth


def calculate_account_health(account: Account) -> AccountHealth:
    """Calculate account health metrics."""
    health = AccountHealth()

    # Decision maker count
    health.decision_maker_count = len(account.decision_makers)

    # Verified emails
    health.verified_emails = sum(
        1 for ch in account.contact_channels
        if ch.kind.endswith("_email") and ch.verification_level in ("VERIFIED", "LIKELY")
    )

    # Verified phones
    health.verified_phones = sum(
        1 for ch in account.contact_channels
        if ch.kind in ("business_phone", "founder_phone") and ch.verification_level in ("VERIFIED", "LIKELY")
    )

    # LinkedIn coverage
    health.linkedin_coverage = any(
        ch.kind == "linkedin_company" for ch in account.contact_channels
    )

    # Evidence count
    health.evidence_count = len(account.evidence_records)

    # Missing data
    missing: list[str] = []
    if not account.decision_makers:
        missing.append("decision_makers")
    if not account.primary_email:
        missing.append("email")
    if not account.primary_phone:
        missing.append("phone")
    if not account.primary_linkedin:
        missing.append("linkedin")
    health.missing_data = missing

    # Completeness percentage
    total_fields = 6  # dm, email, phone, linkedin, evidence, committee
    filled = 0
    if account.decision_makers:
        filled += 1
    if account.primary_email:
        filled += 1
    if account.primary_phone:
        filled += 1
    if account.primary_linkedin:
        filled += 1
    if account.evidence_records:
        filled += 1
    if account.buying_committee.founder:
        filled += 1
    health.completeness_pct = round((filled / total_fields) * 100, 1)

    # Manual review needed
    health.manual_review_needed = (
        not account.decision_makers
        or (not account.primary_email and not account.primary_phone)
    )

    # Sales ready
    health.sales_ready = (
        len(account.decision_makers) > 0
        and (account.primary_email or account.primary_phone)
        and account.primary_linkedin
        and health.completeness_pct >= 60
    )

    return health
