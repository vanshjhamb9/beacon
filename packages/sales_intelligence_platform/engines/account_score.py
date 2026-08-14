"""Account Score Engine - Calculate weighted account score.

Maximum 100 points:
  Decision Makers: 25
  Verified Email:  20
  Verified Phone:  15
  LinkedIn:        10
  Buying Committee: 10
  Evidence:        10
  Completeness:    10
"""

from __future__ import annotations

from packages.sales_intelligence_platform.models import Account, AccountScore


def calculate_account_score(account: Account) -> AccountScore:
    """Calculate the weighted account score."""
    sc = AccountScore()

    # ─── Decision Makers (25 pts) ────────────────────────────────
    dm_count = len(account.decision_makers)
    if dm_count >= 3:
        sc.decision_makers = 25.0
    elif dm_count == 2:
        sc.decision_makers = 20.0
    elif dm_count == 1:
        sc.decision_makers = 15.0
    else:
        sc.decision_makers = 0.0

    # ─── Verified Email (20 pts) ─────────────────────────────────
    email_channels = [ch for ch in account.contact_channels if ch.kind.endswith("_email")]
    verified_emails = [ch for ch in email_channels if ch.verification_level in ("VERIFIED", "LIKELY")]
    if verified_emails:
        sc.verified_email = 20.0
    elif email_channels:
        sc.verified_email = 10.0
    else:
        sc.verified_email = 0.0

    # ─── Verified Phone (15 pts) ─────────────────────────────────
    phone_channels = [ch for ch in account.contact_channels if ch.kind in ("business_phone", "founder_phone")]
    verified_phones = [ch for ch in phone_channels if ch.verification_level in ("VERIFIED", "LIKELY")]
    if verified_phones:
        sc.verified_phone = 15.0
    elif phone_channels:
        sc.verified_phone = 7.0
    else:
        sc.verified_phone = 0.0

    # ─── LinkedIn (10 pts) ───────────────────────────────────────
    has_linkedin = any(ch.kind == "linkedin_company" for ch in account.contact_channels)
    if has_linkedin:
        sc.linkedin = 10.0
    else:
        sc.linkedin = 0.0

    # ─── Buying Committee (10 pts) ───────────────────────────────
    committee = account.buying_committee
    committee_members = sum(1 for m in committee.members if m.get("name"))
    if committee_members >= 3:
        sc.buying_committee = 10.0
    elif committee_members >= 2:
        sc.buying_committee = 7.0
    elif committee_members >= 1:
        sc.buying_committee = 4.0
    else:
        sc.buying_committee = 0.0

    # ─── Evidence (10 pts) ───────────────────────────────────────
    evidence_count = len(account.evidence_records)
    if evidence_count >= 10:
        sc.evidence = 10.0
    elif evidence_count >= 5:
        sc.evidence = 7.0
    elif evidence_count >= 2:
        sc.evidence = 4.0
    else:
        sc.evidence = 1.0

    # ─── Completeness (10 pts) ───────────────────────────────────
    completeness = account.health.completeness_pct if account.health else 0.0
    sc.completeness = min(10.0, completeness / 10.0)

    # ─── Total ───────────────────────────────────────────────────
    sc.total = min(100.0, (
        sc.decision_makers
        + sc.verified_email
        + sc.verified_phone
        + sc.linkedin
        + sc.buying_committee
        + sc.evidence
        + sc.completeness
    ))

    return sc
