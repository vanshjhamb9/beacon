"""Support Gap Engine - Detect customer support operational gaps."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_SUPPORT_GAP = 100.0


def detect_support_gap(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Detect support operational gaps."""
    gaps: list[str] = []
    score = 0.0
    evidence: list[dict] = []

    # No chatbot (+25)
    if not lead_data.get("chatbot_detected", False):
        gaps.append("No automated customer support")
        score += 25.0
        evidence.append({
            "category": "support_gap",
            "signal": "no_automated_support",
            "summary": "No chatbot or automated support system",
            "score_impact": 25.0,
        })

    # Email only support (+15)
    if lead_data.get("email") and not lead_data.get("phone") and not lead_data.get("chatbot_detected", False):
        gaps.append("Email-only support channel")
        score += 15.0
        evidence.append({
            "category": "support_gap",
            "signal": "email_only",
            "summary": "Only email available for customer support",
            "score_impact": 15.0,
        })

    # Phone only support (+15)
    if lead_data.get("phone") and not lead_data.get("email") and not lead_data.get("chatbot_detected", False):
        gaps.append("Phone-only support channel")
        score += 15.0
        evidence.append({
            "category": "support_gap",
            "signal": "phone_only",
            "summary": "Only phone available for customer support",
            "score_impact": 15.0,
        })

    # No WhatsApp support (+15)
    if not lead_data.get("whatsapp_detected", False):
        gaps.append("No WhatsApp support channel")
        score += 15.0
        evidence.append({
            "category": "support_gap",
            "signal": "no_whatsapp_support",
            "summary": "No WhatsApp for customer communication",
            "score_impact": 15.0,
        })

    # Large catalog without support (+15)
    product_count = lead_data.get("product_count", 0)
    if product_count >= 100 and not lead_data.get("chatbot_detected", False):
        gaps.append(f"Large catalog ({product_count} products) with no support automation")
        score += 15.0
        evidence.append({
            "category": "support_gap",
            "signal": "large_catalog_gap",
            "summary": f"{product_count} products but no automated support",
            "score_impact": 15.0,
        })

    # No CRM = no ticket tracking (+10)
    if not lead_data.get("crm_detected", False):
        gaps.append("No CRM for support ticket management")
        score += 10.0
        evidence.append({
            "category": "support_gap",
            "signal": "no_ticket_system",
            "summary": "No CRM or ticketing system for support management",
            "score_impact": 10.0,
        })

    # No multilingual support indicator (+5)
    # This is inferred - Indian brands serving diverse markets need multilingual
    country = lead_data.get("country", "").lower()
    if country == "india" and not lead_data.get("chatbot_detected", False):
        gaps.append("No multilingual support capability detected")
        score += 5.0
        evidence.append({
            "category": "support_gap",
            "signal": "no_multilingual",
            "summary": "Indian brand without multilingual support",
            "score_impact": 5.0,
        })

    intel.support_gap = min(MAX_SUPPORT_GAP, score)
    intel.support_gaps = gaps
    intel.evidence.extend(evidence)
    return intel
