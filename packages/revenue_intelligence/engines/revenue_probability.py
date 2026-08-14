"""Revenue Probability Engine - Calculate probability to buy COMAI.

Deterministic scoring based on all intelligence signals.
Output: probability 0-100 with evidence-backed reasons.
"""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_PROBABILITY = 100.0


def calculate_probability(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Calculate probability to buy COMAI with evidence-backed reasons."""
    reasons: list[str] = []
    score = 0.0

    # ─── ICP Foundation (max 20) ─────────────────────────────────
    if intel.icp_match:
        score += 15.0
        reasons.append("Matches ideal customer profile")
        if intel.icp_score >= 80:
            score += 5.0
            reasons.append("Strong ICP fit")

    # ─── Pain Contribution (max 25) ──────────────────────────────
    if intel.pain_score >= 60:
        score += 25.0
        reasons.append(f"High pain score ({intel.pain_score:.0f}/100)")
    elif intel.pain_score >= 40:
        score += 18.0
        reasons.append(f"Moderate pain score ({intel.pain_score:.0f}/100)")
    elif intel.pain_score >= 20:
        score += 10.0
        reasons.append(f"Some pain detected ({intel.pain_score:.0f}/100)")

    # ─── Technology Gap (max 20) ─────────────────────────────────
    if intel.technology_gap >= 60:
        score += 20.0
        reasons.append("Major technology gap - COMAI fills critical need")
    elif intel.technology_gap >= 40:
        score += 14.0
        reasons.append("Technology gap present")
    elif intel.technology_gap >= 20:
        score += 7.0
        reasons.append("Minor technology gap")

    # ─── Buying Intent (max 20) ──────────────────────────────────
    if intel.buying_intent >= 50:
        score += 20.0
        reasons.append("Strong buying intent signals")
    elif intel.buying_intent >= 30:
        score += 14.0
        reasons.append("Moderate buying intent")
    elif intel.buying_intent >= 15:
        score += 7.0
        reasons.append("Some intent signals")

    # ─── Growth Signal (max 10) ──────────────────────────────────
    if intel.growth_score >= 15:
        score += 10.0
        reasons.append("Growing company - needs scaling solutions")
    elif intel.growth_score >= 8:
        score += 5.0
        reasons.append("Moderate growth signals")

    # ─── Contact Availability (max 5) ────────────────────────────
    if lead_data.get("email") or lead_data.get("phone"):
        score += 5.0
        reasons.append("Contact information available for outreach")

    intel.probability_to_buy = min(MAX_PROBABILITY, score)
    intel.probability_reasons = reasons
    intel.evidence.append({
        "category": "probability",
        "signal": "probability_calculation",
        "summary": f"Probability to buy: {intel.probability_to_buy:.0f}%",
        "score_impact": intel.probability_to_buy,
        "reasons": reasons,
    })

    return intel
