"""Founder Activity Analysis - Detect founder/decision maker signals."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_FOUNDER_SCORE = 100.0


def detect_founder_signals(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Analyze founder/decision maker activity signals."""
    score = 0.0
    evidence: list[dict] = []

    founder_name = lead_data.get("founder_name", "")
    owner_name = lead_data.get("owner_name", "")
    has_linkedin = bool(lead_data.get("linkedin_url", ""))

    # Founder name available = reachable decision maker
    if founder_name:
        score += 40.0
        evidence.append({
            "category": "founder",
            "signal": "founder_identified",
            "summary": f"Founder identified: {founder_name}",
            "score_impact": 40.0,
        })
    elif owner_name:
        score += 30.0
        evidence.append({
            "category": "founder",
            "signal": "owner_identified",
            "summary": f"Owner identified: {owner_name}",
            "score_impact": 30.0,
        })

    # LinkedIn presence = professional network access
    if has_linkedin:
        score += 25.0
        evidence.append({
            "category": "founder",
            "signal": "linkedin_available",
            "summary": "LinkedIn profile available for outreach",
            "score_impact": 25.0,
        })

    # Email available = direct contact
    if lead_data.get("email"):
        score += 20.0
        evidence.append({
            "category": "founder",
            "signal": "email_available",
            "summary": "Direct email available for outreach",
            "score_impact": 20.0,
        })

    # Phone available = direct contact
    if lead_data.get("phone"):
        score += 15.0
        evidence.append({
            "category": "founder",
            "signal": "phone_available",
            "summary": "Phone number available for direct contact",
            "score_impact": 15.0,
        })

    intel.founder_score = min(MAX_FOUNDER_SCORE, score)
    intel.evidence.extend(evidence)
    return intel
