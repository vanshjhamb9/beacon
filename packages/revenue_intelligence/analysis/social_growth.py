"""Social Growth Analysis - Detect social media growth signals."""

from __future__ import annotations

from packages.revenue_intelligence.models import CompanyIntelligence

MAX_SOCIAL_GROWTH = 100.0


def detect_social_growth(
    intel: CompanyIntelligence, lead_data: dict
) -> CompanyIntelligence:
    """Detect social growth indicators."""
    score = 0.0
    evidence: list[dict] = []
    signals: list[str] = []

    social_links = lead_data.get("social_links", {})
    platform_count = len(social_links)

    # Multi-platform presence = active brand building
    if platform_count >= 5:
        score += 40.0
        signals.append(f"Very strong social presence ({platform_count} platforms)")
        evidence.append({
            "category": "social_growth",
            "signal": "multi_platform",
            "summary": f"Active on {platform_count} platforms - strong brand building",
            "score_impact": 40.0,
        })
    elif platform_count >= 3:
        score += 25.0
        signals.append(f"Strong social presence ({platform_count} platforms)")
        evidence.append({
            "category": "social_growth",
            "signal": "good_platform_coverage",
            "summary": f"Active on {platform_count} platforms",
            "score_impact": 25.0,
        })
    elif platform_count >= 2:
        score += 15.0
        signals.append(f"Moderate social presence ({platform_count} platforms)")
        evidence.append({
            "category": "social_growth",
            "signal": "moderate_coverage",
            "summary": f"Active on {platform_count} platforms",
            "score_impact": 15.0,
        })
    elif platform_count == 1:
        score += 5.0

    # Instagram as growth indicator
    if social_links.get("instagram"):
        score += 20.0
        signals.append("Instagram brand presence")
        evidence.append({
            "category": "social_growth",
            "signal": "instagram_growth",
            "summary": "Instagram presence indicates active brand marketing",
            "score_impact": 20.0,
        })

    # Facebook as reach indicator
    if social_links.get("facebook"):
        score += 10.0
        signals.append("Facebook page presence")
        evidence.append({
            "category": "social_growth",
            "signal": "facebook_reach",
            "summary": "Facebook presence for customer reach",
            "score_impact": 10.0,
        })

    # LinkedIn as business maturity
    if social_links.get("linkedin"):
        score += 10.0
        signals.append("LinkedIn company presence")
        evidence.append({
            "category": "social_growth",
            "signal": "linkedin_maturity",
            "summary": "LinkedIn indicates business maturity",
            "score_impact": 10.0,
        })

    # YouTube as content marketing
    if social_links.get("youtube"):
        score += 15.0
        signals.append("YouTube content presence")
        evidence.append({
            "category": "social_growth",
            "signal": "youtube_content",
            "summary": "YouTube presence indicates content marketing investment",
            "score_impact": 15.0,
        })

    intel.social_growth = min(MAX_SOCIAL_GROWTH, score)
    intel.growth_signals.extend(signals)
    intel.evidence.extend(evidence)
    return intel
