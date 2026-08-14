"""Account Reports - Generate reports for accounts."""

from __future__ import annotations

from typing import Any

from packages.sales_intelligence_platform.models import Account


def generate_account_report(account: Account) -> dict[str, Any]:
    """Generate a detailed report for a single account."""
    return {
        "company_name": account.company_name,
        "website": account.website,
        "domain": account.domain,
        "platform": account.platform,
        "category": account.category,
        "status": account.status,
        "score": account.score.__dict__,
        "health": account.health.__dict__,
        "decision_makers": [
            {
                "name": dm.name,
                "role": dm.normalized_role,
                "email": dm.work_email,
                "phone": dm.business_phone,
                "linkedin": dm.linkedin_url,
                "confidence": round(dm.confidence, 2),
                "source": dm.source,
            }
            for dm in account.decision_makers
        ],
        "contact_channels": [
            {
                "kind": ch.kind,
                "value": ch.value,
                "verification": ch.verification_level,
                "confidence": round(ch.confidence, 2),
            }
            for ch in account.contact_channels
        ],
        "buying_committee": {
            "trigger": account.buying_committee.trigger,
            "founder": account.buying_committee.founder,
            "operations": account.buying_committee.operations,
            "technology": account.buying_committee.technology,
            "growth": account.buying_committee.growth,
        },
        "evidence_summary": {
            "total": len(account.evidence_records),
            "verified": sum(
                1 for e in account.evidence_records
                if e.verification_status in ("VERIFIED", "LIKELY")
            ),
        },
    }
