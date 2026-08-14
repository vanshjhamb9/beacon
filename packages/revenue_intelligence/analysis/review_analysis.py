"""Review Analysis Engine - Detect support complaint signals."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_REVIEW_SCORE = 100.0


def detect_review_signals(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Detect review-based pain signals from observable data."""
    score = 0.0
    evidence: list[dict] = []

    # No chatbot often correlates with poor support reviews
    if not lead_data.get("chatbot_detected", False):
        score += 30.0
        evidence.append({
            "category": "review",
            "signal": "no_support_automation",
            "summary": "No chatbot suggests potential support quality issues",
            "score_impact": 30.0,
        })

    # Email-only support often gets poor reviews
    if lead_data.get("email") and not lead_data.get("chatbot_detected", False):
        score += 20.0
        evidence.append({
            "category": "review",
            "signal": "limited_support_channels",
            "summary": "Limited support channels may lead to poor reviews",
            "score_impact": 20.0,
        })

    # Large catalog without support = more complaints
    product_count = lead_data.get("product_count", 0)
    if product_count >= 100 and not lead_data.get("chatbot_detected", False):
        score += 25.0
        evidence.append({
            "category": "review",
            "signal": "catalog_complaint_risk",
            "summary": f"{product_count} products without support automation increases complaint risk",
            "score_impact": 25.0,
        })

    # Fashion/beauty have inherently high return rates
    category = lead_data.get("category", "").lower()
    high_return_categories = ["fashion", "beauty", "cosmetics", "jewellery"]
    if any(cat in category for cat in high_return_categories):
        score += 15.0
        evidence.append({
            "category": "review",
            "signal": "high_return_category",
            "summary": f"'{lead_data.get('category')}' has inherently high return rates",
            "score_impact": 15.0,
        })

    intel.review_score = min(MAX_REVIEW_SCORE, score)
    intel.evidence.extend(evidence)
    return intel
