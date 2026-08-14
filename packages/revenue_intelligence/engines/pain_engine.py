"""Pain Engine - Detect customer support pain signals.

Every signal adds deterministic score. No GPT dependency.
"""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_PAIN_SCORE = 100.0


def detect_pain(intel: CompanyIntelligence, lead_data: dict) -> CompanyIntelligence:
    """Detect all pain signals and calculate pain score."""
    signals: list[str] = []
    score = 0.0
    evidence: list[dict] = []

    # No chatbot detected (+20)
    if not lead_data.get("chatbot_detected", False):
        signals.append("No chatbot detected")
        score += 20.0
        evidence.append({
            "category": "pain",
            "signal": "no_chatbot",
            "summary": "No customer support chatbot on website",
            "score_impact": 20.0,
        })

    # No WhatsApp automation (+15)
    if not lead_data.get("whatsapp_detected", False):
        signals.append("No WhatsApp presence")
        score += 15.0
        evidence.append({
            "category": "pain",
            "signal": "no_whatsapp",
            "summary": "No WhatsApp integration detected",
            "score_impact": 15.0,
        })
    elif lead_data.get("whatsapp_detected", False) and not lead_data.get("crm_detected", False):
        signals.append("WhatsApp exists but no CRM automation")
        score += 10.0
        evidence.append({
            "category": "pain",
            "signal": "whatsapp_no_crm",
            "summary": "WhatsApp present but no CRM integration",
            "score_impact": 10.0,
        })

    # No CRM detected (+15)
    if not lead_data.get("crm_detected", False):
        signals.append("No CRM system detected")
        score += 15.0
        evidence.append({
            "category": "pain",
            "signal": "no_crm",
            "summary": "No CRM system detected on website",
            "score_impact": 15.0,
        })

    # Large catalog without support (+10)
    product_count = lead_data.get("product_count", 0)
    if product_count >= 100:
        signals.append(f"Large catalog ({product_count}+ products) without adequate support")
        score += 10.0
        evidence.append({
            "category": "pain",
            "signal": "large_catalog_no_support",
            "summary": f"{product_count} products but no chatbot or helpdesk",
            "score_impact": 10.0,
        })

    # No AI support (+10)
    if not lead_data.get("chatbot_detected", False) and not lead_data.get("crm_detected", False):
        signals.append("No AI-powered support tools")
        score += 10.0
        evidence.append({
            "category": "pain",
            "signal": "no_ai_support",
            "summary": "No AI or automation tools detected",
            "score_impact": 10.0,
        })

    # Support email only (+5)
    if lead_data.get("email") and not lead_data.get("phone"):
        signals.append("Support contact limited to email only")
        score += 5.0
        evidence.append({
            "category": "pain",
            "signal": "email_only_support",
            "summary": "Only email provided for customer support",
            "score_impact": 5.0,
        })

    # Support phone only (+5)
    if lead_data.get("phone") and not lead_data.get("email"):
        signals.append("Support contact limited to phone only")
        score += 5.0
        evidence.append({
            "category": "pain",
            "signal": "phone_only_support",
            "summary": "Only phone number provided for support",
            "score_impact": 5.0,
        })

    # High SKU count (+8)
    if product_count >= 200:
        signals.append(f"High SKU count ({product_count}) - complex inventory management")
        score += 8.0
        evidence.append({
            "category": "pain",
            "signal": "high_sku_count",
            "summary": f"Very large product catalog ({product_count} items)",
            "score_impact": 8.0,
        })

    # D2C category complexity (+7)
    category = lead_data.get("category", "").lower()
    complex_categories = ["fashion", "beauty", "cosmetics", "supplements", "jewellery"]
    if any(cat in category for cat in complex_categories):
        signals.append(f"Complex category ({lead_data.get('category')}) - high support needs")
        score += 7.0
        evidence.append({
            "category": "pain",
            "signal": "complex_category",
            "summary": f"Industry '{lead_data.get('category')}' requires high customer support",
            "score_impact": 7.0,
        })

    # Magento detected (+5) - legacy platform pain
    if lead_data.get("magento_detected", False):
        signals.append("Magento platform - higher maintenance burden")
        score += 5.0
        evidence.append({
            "category": "pain",
            "signal": "magento_legacy",
            "summary": "Magento platform detected - higher maintenance and support costs",
            "score_impact": 5.0,
        })

    intel.pain_score = min(MAX_PAIN_SCORE, score)
    intel.pain_signals = signals
    intel.evidence.extend(evidence)
    return intel
