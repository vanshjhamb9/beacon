"""Priority Engine - Classify lead priority for COMAI outreach."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence


def classify_priority(intel: CompanyIntelligence) -> CompanyIntelligence:
    """Classify lead into priority tiers based on all intelligence."""
    score = intel.probability_to_buy
    icp = intel.icp_match
    pain = intel.pain_score
    growth = intel.growth_score

    if not icp:
        intel.priority = "REJECT"
    elif score >= 80 and pain >= 50:
        intel.priority = "URGENT"
    elif score >= 70:
        intel.priority = "HOT"
    elif score >= 50:
        intel.priority = "WARM"
    elif score >= 30:
        intel.priority = "NURTURE"
    else:
        intel.priority = "LOW"

    intel.evidence.append({
        "category": "priority",
        "signal": "priority_classification",
        "summary": f"Priority: {intel.priority} (probability: {score:.0f}%)",
        "score_impact": 0.0,
    })

    return intel
