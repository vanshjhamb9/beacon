"""ICP Engine - Ideal Customer Profile matching.

Reject enterprise brands, marketplace giants, government, banks, airlines.
Accept growing D2C, Shopify/WooCommerce stores, 5-250 employees, Indian brands.
"""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

# ─── REJECTION LISTS ───────────────────────────────────────────────

REJECTED_DOMAINS: set[str] = {
    # Global enterprise brands
    "levi.com", "levis.co.in", "nike.com", "nike.co.in",
    "adidas.com", "adidas.co.in", "puma.com", "puma.co.in",
    "apple.com", "samsung.com", "samsung.in",
    "hm.com", "zara.com", "uniqlo.com",
    "amazon.in", "amazon.com", "flipkart.com",
    "myntra.com", "ajio.com", "tatacliq.com",
    "jiomart.com", "bigbasket.com", "swiggy.com", "zomato.com",
    "paytm.com", "phonepe.com", "google.com", "microsoft.com",
    "meta.com", "facebook.com", "instagram.com",
    # Government / Banks / Airlines
    "gov.in", "nic.in", "sbi.co.in", "hdfcbank.com",
    "icicibank.com", "axisbank.com", "kotak.com",
    "indigo.in", "airindia.com", "spicejet.com",
    "vistara.com", "goindigo.in",
}

REJECTED_NAMES: set[str] = {
    "levis", "nike", "adidas", "puma", "apple", "samsung",
    "h&m", "zara", "uniqlo", "amazon", "flipkart",
    "myntra", "ajio", "tata cliq", "jiomart",
    "bigbasket", "swiggy", "zomato",
    "paytm", "phonepe", "google", "microsoft",
    "sbi", "hdfc", "icici", "axis bank", "kotak",
    "indigo", "air india", "spicejet", "vistara",
    "govt", "government",
}

# ─── ACCEPTANCE CRITERIA ──────────────────────────────────────────

D2C_CATEGORIES: set[str] = {
    "beauty", "skincare", "cosmetics", "fashion", "supplements",
    "grooming", "wellness", "personal care", "organic",
    "health", "fitness", "nutrition", "home decor",
    "jewellery", "accessories", "kids", "pet supplies",
    "tea", "coffee", "food", "beverages",
}

SHOPIFY_CATEGORIES: set[str] = {
    "shopify", "d2c", "direct to consumer", "direct-to-consumer",
}


def match_icp(intel: CompanyIntelligence, lead_data: dict) -> CompanyIntelligence:
    """Determine ICP match and rejection status."""
    rejection_reasons: list[str] = []
    acceptance_reasons: list[str] = []

    domain = lead_data.get("domain", "").lower()
    company_name = lead_data.get("company_name", "").lower()
    category = lead_data.get("category", "").lower()
    platform = lead_data.get("platform", "").lower()
    product_count = lead_data.get("product_count", 0)
    country = lead_data.get("country", "").lower()

    # ─── REJECTION CHECKS ────────────────────────────────────────

    # Reject known enterprise domains
    for rejected in REJECTED_DOMAINS:
        if rejected in domain:
            rejection_reasons.append(f"Enterprise domain detected: {rejected}")
            break

    # Reject known enterprise names
    for rejected in REJECTED_NAMES:
        if rejected in company_name:
            rejection_reasons.append(f"Enterprise brand detected: {rejected}")
            break

    # Reject marketplace giants
    marketplace_indicators = ["marketplace", "multi-vendor", "multi seller"]
    description = lead_data.get("description", "").lower()
    if any(ind in description for ind in marketplace_indicators):
        rejection_reasons.append("Marketplace/multi-vendor business model")

    # Reject government/bank/airline TLDs
    government_tlds = [".gov.in", ".nic.in", ".gov"]
    if any(tld in domain for tld in government_tlds):
        rejection_reasons.append("Government domain")

    bank_indicators = ["bank", "financial", "insurance", "nbfc"]
    if any(ind in company_name for ind in bank_indicators):
        rejection_reasons.append("Financial institution")

    airline_indicators = ["airline", "airways", "aviation", "fly"]
    if any(ind in company_name for ind in airline_indicators):
        rejection_reasons.append("Airline company")

    # Reject non-Indian if targeting India
    if country != "india":
        rejection_reasons.append(f"Not an Indian company (country: {country})")

    # ─── ACCEPTANCE CHECKS ───────────────────────────────────────

    # D2C category match
    if any(cat in category for cat in D2C_CATEGORIES):
        acceptance_reasons.append(f"D2C category match: {lead_data.get('category')}")

    # Shopify/WooCommerce platform
    if platform in ("shopify", "woocommerce"):
        acceptance_reasons.append(f"Ecommerce platform: {platform.title()}")

    # Indian company
    if country == "india":
        acceptance_reasons.append("Indian company")

    # Growing product catalog
    if product_count >= 10:
        acceptance_reasons.append(f"Active catalog: {product_count} products")

    # Has social presence
    social_links = lead_data.get("social_links", {})
    if len(social_links) >= 2:
        acceptance_reasons.append(f"Social presence: {len(social_links)} platforms")

    # ─── ICP SCORE ───────────────────────────────────────────────

    is_rejected = len(rejection_reasons) > 0
    icp_score = 0.0

    if not is_rejected:
        icp_score = 50.0  # Base score for non-rejected
        icp_score += min(20.0, len(acceptance_reasons) * 10.0)
        if platform in ("shopify", "woocommerce"):
            icp_score += 15.0
        if any(cat in category for cat in D2C_CATEGORIES):
            icp_score += 15.0
        icp_score = min(100.0, icp_score)
    else:
        icp_score = 0.0

    intel.icp_match = not is_rejected
    intel.icp_score = icp_score
    intel.icp_reasons = acceptance_reasons
    intel.rejection_reasons = rejection_reasons
    intel.evidence.append({
        "category": "icp",
        "signal": "icp_evaluation",
        "summary": f"ICP match: {not is_rejected}, score: {icp_score:.0f}",
        "score_impact": icp_score,
        "accepted": acceptance_reasons,
        "rejected": rejection_reasons,
    })

    return intel
