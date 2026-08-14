"""Traffic Signals Engine - Infer traffic from observable signals."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_TRAFFIC_SCORE = 100.0


def detect_traffic_signals(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Infer traffic level from observable signals."""
    score = 0.0
    evidence: list[dict] = []

    # Product count as traffic proxy
    product_count = lead_data.get("product_count", 0)
    if product_count >= 200:
        score += 30.0
        evidence.append({
            "category": "traffic",
            "signal": "large_catalog",
            "summary": f"Large catalog ({product_count} products) drives organic traffic",
            "score_impact": 30.0,
        })
    elif product_count >= 50:
        score += 20.0
        evidence.append({
            "category": "traffic",
            "signal": "medium_catalog",
            "summary": f"Medium catalog ({product_count} products)",
            "score_impact": 20.0,
        })
    elif product_count >= 10:
        score += 10.0
        evidence.append({
            "category": "traffic",
            "signal": "small_catalog",
            "summary": f"Catalog of {product_count} products",
            "score_impact": 10.0,
        })

    # Social media presence as traffic source
    social_links = lead_data.get("social_links", {})
    if len(social_links) >= 4:
        score += 25.0
        evidence.append({
            "category": "traffic",
            "signal": "strong_social_traffic",
            "summary": f"{len(social_links)} social platforms drive traffic",
            "score_impact": 25.0,
        })
    elif len(social_links) >= 2:
        score += 15.0
        evidence.append({
            "category": "traffic",
            "signal": "moderate_social_traffic",
            "summary": f"{len(social_links)} social platforms",
            "score_impact": 15.0,
        })
    elif len(social_links) >= 1:
        score += 5.0

    # Platform SEO capabilities
    platform = lead_data.get("platform", "").lower()
    if platform == "shopify":
        score += 15.0
        evidence.append({
            "category": "traffic",
            "signal": "shopify_seo",
            "summary": "Shopify platform has strong SEO capabilities",
            "score_impact": 15.0,
        })
    elif platform == "woocommerce":
        score += 12.0
        evidence.append({
            "category": "traffic",
            "signal": "woocommerce_seo",
            "summary": "WooCommerce has good SEO capabilities",
            "score_impact": 12.0,
        })

    # Instagram as traffic driver
    if social_links.get("instagram"):
        score += 10.0
        evidence.append({
            "category": "traffic",
            "signal": "instagram_traffic",
            "summary": "Instagram presence drives discovery traffic",
            "score_impact": 10.0,
        })

    # Category traffic potential
    category = lead_data.get("category", "").lower()
    high_traffic_categories = ["fashion", "beauty", "skincare", "electronics"]
    if any(cat in category for cat in high_traffic_categories):
        score += 10.0
        evidence.append({
            "category": "traffic",
            "signal": "high_traffic_category",
            "summary": f"'{lead_data.get('category')}' is a high-traffic category",
            "score_impact": 10.0,
        })

    intel.traffic_score = min(MAX_TRAFFIC_SCORE, score)
    intel.evidence.extend(evidence)
    return intel
