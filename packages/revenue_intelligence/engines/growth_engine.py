"""Growth Engine - Detect company growth signals.

Score: 0-25
"""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_GROWTH_SCORE = 25.0


def detect_growth(intel: CompanyIntelligence, lead_data: dict) -> CompanyIntelligence:
    """Detect growth signals and calculate growth score."""
    signals: list[str] = []
    score = 0.0
    evidence: list[dict] = []

    # Social presence as growth proxy (+5 per platform, max 15)
    social_links = lead_data.get("social_links", {})
    platform_count = len(social_links)
    if platform_count >= 4:
        signals.append(f"Strong social presence ({platform_count} platforms)")
        score += 15.0
        evidence.append({
            "category": "growth",
            "signal": "strong_social",
            "summary": f"Active on {platform_count} social platforms",
            "score_impact": 15.0,
        })
    elif platform_count >= 2:
        signals.append(f"Active on {platform_count} social platforms")
        score += 8.0
        evidence.append({
            "category": "growth",
            "signal": "moderate_social",
            "summary": f"Active on {platform_count} social platforms",
            "score_impact": 8.0,
        })
    elif platform_count >= 1:
        signals.append("Some social presence")
        score += 3.0
        evidence.append({
            "category": "growth",
            "signal": "minimal_social",
            "summary": "Active on 1 social platform",
            "score_impact": 3.0,
        })

    # Product count as expansion proxy (+5)
    product_count = lead_data.get("product_count", 0)
    if product_count >= 50:
        signals.append(f"Growing product catalog ({product_count} products)")
        score += 5.0
        evidence.append({
            "category": "growth",
            "signal": "product_expansion",
            "summary": f"Catalog of {product_count} products indicates growth",
            "score_impact": 5.0,
        })
    elif product_count >= 20:
        signals.append(f"Moderate catalog ({product_count} products)")
        score += 3.0
        evidence.append({
            "category": "growth",
            "signal": "moderate_catalog",
            "summary": f"Catalog of {product_count} products",
            "score_impact": 3.0,
        })

    # Instagram presence as brand growth (+3)
    if social_links.get("instagram"):
        signals.append("Instagram brand presence")
        score += 3.0
        evidence.append({
            "category": "growth",
            "signal": "instagram_brand",
            "summary": "Active Instagram brand presence",
            "score_impact": 3.0,
        })

    # LinkedIn presence as corporate growth (+2)
    if social_links.get("linkedin"):
        signals.append("LinkedIn company presence")
        score += 2.0
        evidence.append({
            "category": "growth",
            "signal": "linkedin_presence",
            "summary": "Active LinkedIn company page",
            "score_impact": 2.0,
        })

    # Platform indicators
    platform = lead_data.get("platform", "").lower()
    if platform == "shopify":
        signals.append("Shopify platform - fast growing ecosystem")
        score += 2.0
        evidence.append({
            "category": "growth",
            "signal": "shopify_platform",
            "summary": "Shopify platform indicates modern tech adoption",
            "score_impact": 2.0,
        })

    intel.growth_score = min(MAX_GROWTH_SCORE, score)
    intel.growth_signals = signals
    intel.evidence.extend(evidence)
    return intel
