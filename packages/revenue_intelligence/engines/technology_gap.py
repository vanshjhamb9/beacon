"""Technology Gap Engine - Detect missing technology that COMAI can fill."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_TECH_GAP = 100.0


def detect_technology_gap(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Detect technology gaps and calculate gap score."""
    gaps: list[str] = []
    score = 0.0
    evidence: list[dict] = []

    # No chatbot (+30)
    if not lead_data.get("chatbot_detected", False):
        gaps.append("No chatbot")
        score += 30.0
        evidence.append({
            "category": "technology_gap",
            "signal": "no_chatbot",
            "summary": "No customer support chatbot detected",
            "score_impact": 30.0,
        })

    # No WhatsApp integration (+20)
    if not lead_data.get("whatsapp_detected", False):
        gaps.append("No WhatsApp integration")
        score += 20.0
        evidence.append({
            "category": "technology_gap",
            "signal": "no_whatsapp",
            "summary": "No WhatsApp business integration",
            "score_impact": 20.0,
        })

    # No CRM (+20)
    if not lead_data.get("crm_detected", False):
        gaps.append("No CRM system")
        score += 20.0
        evidence.append({
            "category": "technology_gap",
            "signal": "no_crm",
            "summary": "No CRM system detected",
            "score_impact": 20.0,
        })

    # No helpdesk (+15)
    if not lead_data.get("chatbot_detected", False) and not lead_data.get("crm_detected", False):
        gaps.append("No helpdesk or support system")
        score += 15.0
        evidence.append({
            "category": "technology_gap",
            "signal": "no_helpdesk",
            "summary": "No helpdesk or ticketing system detected",
            "score_impact": 15.0,
        })

    # Legacy platform (+10)
    platform = lead_data.get("platform", "").lower()
    if platform == "magento":
        gaps.append("Magento - legacy platform with high maintenance")
        score += 10.0
        evidence.append({
            "category": "technology_gap",
            "signal": "legacy_platform",
            "summary": "Magento detected - legacy ecommerce platform",
            "score_impact": 10.0,
        })

    # No AI tools (+5)
    if not lead_data.get("chatbot_detected", False):
        gaps.append("No AI-powered tools detected")
        score += 5.0
        evidence.append({
            "category": "technology_gap",
            "signal": "no_ai",
            "summary": "No AI or ML tools detected on website",
            "score_impact": 5.0,
        })

    intel.technology_gap = min(MAX_TECH_GAP, score)
    intel.tech_gaps = gaps
    intel.evidence.extend(evidence)
    return intel
