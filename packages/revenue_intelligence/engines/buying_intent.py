"""Buying Intent Engine - Detect signals that indicate purchase readiness.

Strong buying signals only. No weak signals.
"""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_BUYING_INTENT = 100.0


def detect_buying_intent(
    intel: CompanyIntelligence, lead_data: dict, pain_score: float, growth_score: float
) -> CompanyIntelligence:
    """Detect buying intent signals."""
    signals: list[str] = []
    score = 0.0
    evidence: list[dict] = []

    # High pain without solutions = buying intent (+30)
    if pain_score >= 50 and not lead_data.get("chatbot_detected", False):
        signals.append("High customer support pain with no existing solution")
        score += 30.0
        evidence.append({
            "category": "intent",
            "signal": "high_pain_no_solution",
            "summary": f"Pain score {pain_score:.0f} with no chatbot/CRM",
            "score_impact": 30.0,
        })

    # Growing company without automation (+25)
    if growth_score >= 15 and not lead_data.get("crm_detected", False):
        signals.append("Growing company without CRM automation")
        score += 25.0
        evidence.append({
            "category": "intent",
            "signal": "growing_no_automation",
            "summary": f"Growth score {growth_score:.0f} but no CRM",
            "score_impact": 25.0,
        })

    # WhatsApp without automation (+15)
    if lead_data.get("whatsapp_detected", False) and not lead_data.get("crm_detected", False):
        signals.append("Uses WhatsApp but no automation - scaling pain")
        score += 15.0
        evidence.append({
            "category": "intent",
            "signal": "whatsapp_manual",
            "summary": "WhatsApp present but not automated",
            "score_impact": 15.0,
        })

    # No chatbot + large catalog (+10)
    product_count = lead_data.get("product_count", 0)
    if product_count >= 50 and not lead_data.get("chatbot_detected", False):
        signals.append(f"Large catalog ({product_count} products) needs automated support")
        score += 10.0
        evidence.append({
            "category": "intent",
            "signal": "catalog_needs_support",
            "summary": f"{product_count} products without chatbot",
            "score_impact": 10.0,
        })

    # Shopify + no support tools (+10)
    if lead_data.get("shopify_detected", False) and not lead_data.get("chatbot_detected", False):
        signals.append("Shopify store without support tools - COMAI fits ecosystem")
        score += 10.0
        evidence.append({
            "category": "intent",
            "signal": "shopify_gap",
            "summary": "Shopify store with no chatbot or helpdesk",
            "score_impact": 10.0,
        })

    # D2C brand + no CRM (+10)
    category = lead_data.get("category", "").lower()
    d2c_categories = ["beauty", "skincare", "cosmetics", "fashion", "supplements", "grooming", "wellness"]
    if any(cat in category for cat in d2c_categories) and not lead_data.get("crm_detected", False):
        signals.append(f"D2C brand in '{lead_data.get('category')}' without CRM")
        score += 10.0
        evidence.append({
            "category": "intent",
            "signal": "d2c_no_crm",
            "summary": f"D2C brand ({lead_data.get('category')}) needs CRM",
            "score_impact": 10.0,
        })

    intel.buying_intent = min(MAX_BUYING_INTENT, score)
    intel.intent_signals = signals
    intel.evidence.extend(evidence)
    return intel
