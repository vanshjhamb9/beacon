"""Company Summary Engine - Generate why_comai, recommended_pitch, and revenue_potential."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

# ─── REVENUE POTENTIAL BY CATEGORY ────────────────────────────────

CATEGORY_REVENUE: dict[str, float] = {
    "beauty": 85.0,
    "skincare": 85.0,
    "cosmetics": 80.0,
    "fashion": 75.0,
    "supplements": 90.0,
    "grooming": 80.0,
    "wellness": 85.0,
    "personal care": 80.0,
    "organic": 75.0,
    "health": 85.0,
    "fitness": 70.0,
    "nutrition": 80.0,
    "home decor": 65.0,
    "jewellery": 70.0,
    "accessories": 60.0,
    "kids": 65.0,
    "pet supplies": 60.0,
    "tea": 55.0,
    "coffee": 55.0,
    "food": 60.0,
    "beverages": 55.0,
    "electronics": 50.0,
    "marketplace": 40.0,
}


def generate_summary(intel: CompanyIntelligence, lead_data: dict) -> CompanyIntelligence:
    """Generate company summary, why_comai, recommended_pitch, revenue_potential."""
    category = lead_data.get("category", "").lower()
    company = intel.company_name
    pain_count = len(intel.pain_signals)
    gap_count = len(intel.tech_gaps)

    # ─── Revenue Potential ────────────────────────────────────────
    base_revenue = CATEGORY_REVENUE.get(category, 50.0)
    product_multiplier = min(1.5, 1.0 + (lead_data.get("product_count", 0) / 200.0))
    growth_multiplier = min(1.3, 1.0 + (intel.growth_score / 100.0))
    intel.revenue_potential = min(100.0, base_revenue * product_multiplier * growth_multiplier)

    # ─── Why COMAI ────────────────────────────────────────────────
    why_parts: list[str] = []
    if intel.pain_score >= 40:
        why_parts.append(f"has significant customer support pain ({pain_count} signals detected)")
    if intel.technology_gap >= 40:
        why_parts.append(f"has major technology gaps ({gap_count} gaps)")
    if intel.growth_score >= 10:
        why_parts.append("is actively growing and needs scalable solutions")
    if intel.whatsapp_score >= 40:
        why_parts.append("can benefit from WhatsApp automation")
    if intel.founder_score >= 40:
        why_parts.append("has identifiable decision makers for direct outreach")

    if why_parts:
        intel.why_comai = f"{company} {', '.join(why_parts[:3])}."
    else:
        intel.why_comai = f"{company} matches COMAI's target customer profile."

    # ─── Recommended Pitch ────────────────────────────────────────
    pitch_parts: list[str] = []
    if not lead_data.get("chatbot_detected", False):
        pitch_parts.append("automated customer support with AI chatbot")
    if not lead_data.get("whatsapp_detected", False):
        pitch_parts.append("WhatsApp business automation")
    if not lead_data.get("crm_detected", False):
        pitch_parts.append("integrated CRM for customer management")
    if lead_data.get("product_count", 0) >= 50:
        pitch_parts.append("scalable support for growing catalog")

    if pitch_parts:
        intel.recommended_pitch = f"Lead with {', '.join(pitch_parts[:2])}."
    else:
        intel.recommended_pitch = "Position COMAI as upgrade to existing support stack."

    return intel
