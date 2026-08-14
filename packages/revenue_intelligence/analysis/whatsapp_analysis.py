"""WhatsApp Analysis - Detect WhatsApp usage patterns."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_WHATSAPP_SCORE = 100.0


def detect_whatsapp_signals(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Analyze WhatsApp usage and automation gaps."""
    score = 0.0
    evidence: list[dict] = []

    has_whatsapp = lead_data.get("whatsapp_detected", False)
    has_crm = lead_data.get("crm_detected", False)
    has_chatbot = lead_data.get("chatbot_detected", False)

    if has_whatsapp and not has_crm and not has_chatbot:
        # WhatsApp present but no automation = scaling pain
        score += 60.0
        evidence.append({
            "category": "whatsapp",
            "signal": "whatsapp_no_automation",
            "summary": "WhatsApp present but no CRM/chatbot automation - manual scaling pain",
            "score_impact": 60.0,
        })
    elif has_whatsapp and has_crm:
        # Already has some automation
        score += 20.0
        evidence.append({
            "category": "whatsapp",
            "signal": "whatsapp_with_crm",
            "summary": "WhatsApp with CRM - potential for COMAI upgrade",
            "score_impact": 20.0,
        })
    elif not has_whatsapp:
        # No WhatsApp = opportunity to introduce
        score += 30.0
        evidence.append({
            "category": "whatsapp",
            "signal": "no_whatsapp",
            "summary": "No WhatsApp - opportunity to introduce COMAI WhatsApp solution",
            "score_impact": 30.0,
        })

    # Indian brands especially need WhatsApp
    country = lead_data.get("country", "").lower()
    if country == "india" and not has_whatsapp:
        score += 20.0
        evidence.append({
            "category": "whatsapp",
            "signal": "indian_no_whatsapp",
            "summary": "Indian brand without WhatsApp - critical gap for customer communication",
            "score_impact": 20.0,
        })

    intel.whatsapp_score = min(MAX_WHATSAPP_SCORE, score)
    intel.evidence.extend(evidence)
    return intel
