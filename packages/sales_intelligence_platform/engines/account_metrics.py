"""Account Metrics - Calculate aggregate metrics across accounts."""

from __future__ import annotations

from typing import Any

from packages.sales_intelligence_platform.models import Account


def calculate_metrics(accounts: list[Account]) -> dict[str, Any]:
    """Calculate aggregate metrics across all accounts."""
    total = len(accounts)
    if total == 0:
        return {"total": 0, "avg_score": 0, "avg_completeness": 0}

    scores = [a.score.total for a in accounts]
    completeness = [a.health.completeness_pct for a in accounts]

    return {
        "total": total,
        "avg_score": round(sum(scores) / total, 1),
        "avg_completeness": round(sum(completeness) / total, 1),
        "max_score": round(max(scores), 1),
        "min_score": round(min(scores), 1),
        "sales_ready_pct": round(
            sum(1 for a in accounts if a.status == "SALES_READY") / total * 100, 1
        ),
        "high_confidence_pct": round(
            sum(1 for a in accounts if a.score.total >= 70) / total * 100, 1
        ),
    }
