"""Account Dashboard - Generate dashboard data for SIDP."""

from __future__ import annotations

from typing import Any

from packages.sales_intelligence_platform.models import Account


def generate_dashboard_data(accounts: list[Account]) -> dict[str, Any]:
    """Generate dashboard summary data from accounts."""
    total = len(accounts)

    sales_ready = [a for a in accounts if a.status == "SALES_READY"]
    needs_enrichment = [a for a in accounts if a.status == "NEEDS_ENRICHMENT"]
    manual_review = [a for a in accounts if a.status == "MANUAL_REVIEW"]

    # Top buyers (by score)
    top_buyers = sorted(accounts, key=lambda a: a.score.total, reverse=True)[:10]

    # Top pain companies
    top_pain = sorted(accounts, key=lambda a: a.pain_score, reverse=True)[:10]

    # Highest probability
    highest_prob = sorted(
        [a for a in accounts if a.probability_to_buy > 0],
        key=lambda a: a.probability_to_buy,
        reverse=True,
    )[:10]

    # Missing data summary
    missing_email = [a for a in accounts if not a.primary_email]
    missing_phone = [a for a in accounts if not a.primary_phone]
    missing_dm = [a for a in accounts if not a.decision_makers]

    # Platform distribution
    platforms: dict[str, int] = {}
    for a in accounts:
        p = a.platform or "unknown"
        platforms[p] = platforms.get(p, 0) + 1

    # Category distribution
    categories: dict[str, int] = {}
    for a in accounts:
        c = a.category or "unknown"
        categories[c] = categories.get(c, 0) + 1

    return {
        "total_accounts": total,
        "sales_ready": len(sales_ready),
        "needs_enrichment": len(needs_enrichment),
        "manual_review": len(manual_review),
        "top_buyers": [_account_summary(a) for a in top_buyers],
        "top_pain": [_account_summary(a) for a in top_pain],
        "highest_probability": [_account_summary(a) for a in highest_prob],
        "missing_email_count": len(missing_email),
        "missing_phone_count": len(missing_phone),
        "missing_dm_count": len(missing_dm),
        "platforms": platforms,
        "categories": categories,
        "avg_score": round(
            sum(a.score.total for a in accounts) / max(total, 1), 1
        ),
    }


def _account_summary(account: Account) -> dict[str, Any]:
    return {
        "id": account.id,
        "company_name": account.company_name,
        "domain": account.domain,
        "platform": account.platform,
        "status": account.status,
        "score": round(account.score.total, 1),
        "primary_email": account.primary_email,
        "primary_phone": account.primary_phone,
        "decision_maker": account.primary_decision_maker,
    }
