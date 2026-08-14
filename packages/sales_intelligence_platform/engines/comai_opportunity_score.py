"""COMAI Opportunity Score - deterministic 0-100 scoring engine.

Scores leads based on technology fit, support complexity, WhatsApp presence,
store size, product count, growth signals, social activity, chatbot gap, and FAQ size.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpportunityScore:
    """COMAI opportunity score with component breakdown."""
    total_score: float = 0.0
    technology_fit: float = 0.0
    support_complexity: float = 0.0
    whatsapp_presence: float = 0.0
    store_size: float = 0.0
    product_count_score: float = 0.0
    growth_signals: float = 0.0
    social_activity: float = 0.0
    chatbot_gap: float = 0.0
    faq_size: float = 0.0
    confidence: float = 0.0
    classification: str = ""  # hot, warm, cold
    score_breakdown: dict[str, float] | None = None

    def __post_init__(self):
        if self.score_breakdown is None:
            self.score_breakdown = {}


class COMAIOpportunityScorer:
    """Score leads for COMAI opportunity using deterministic rules."""

    # Weight factors for each component
    WEIGHTS = {
        "technology_fit": 0.15,
        "support_complexity": 0.15,
        "whatsapp_presence": 0.10,
        "store_size": 0.10,
        "product_count": 0.10,
        "growth_signals": 0.10,
        "social_activity": 0.10,
        "chatbot_gap": 0.15,
        "faq_size": 0.05,
    }

    def score(
        self,
        *,
        platform: str = "",
        has_chatbot: bool = False,
        chatbot_tool: str = "",
        has_whatsapp_widget: bool = False,
        has_live_chat: bool = False,
        product_count: int = 0,
        has_ecommerce: bool = True,
        category: str = "",
        instagram_followers: int = 0,
        facebook_likes: int = 0,
        instagram_url: str = "",
        facebook_url: str = "",
        description: str = "",
        founded_year: int = 0,
        city: str = "",
    ) -> OpportunityScore:
        """Calculate COMAI opportunity score."""
        result = OpportunityScore()
        breakdown = {}

        # Technology fit (0-100)
        tech_score = 50.0
        platform_scores = {"shopify": 90, "woocommerce": 80, "magento": 70, "bigcommerce": 75}
        tech_score = platform_scores.get(platform.lower(), 50)
        if not has_chatbot:
            tech_score = min(100, tech_score + 20)
        result.technology_fit = tech_score
        breakdown["technology_fit"] = tech_score

        # Support complexity (0-100) - higher = more complex = more opportunity
        support_score = 30.0
        if not has_chatbot:
            support_score += 40
        if not has_live_chat:
            support_score += 15
        if product_count > 100:
            support_score += 15
        result.support_complexity = min(100, support_score)
        breakdown["support_complexity"] = result.support_complexity

        # WhatsApp presence (0-100)
        whatsapp_score = 80.0 if has_whatsapp_widget else 20.0
        result.whatsapp_presence = whatsapp_score
        breakdown["whatsapp_presence"] = whatsapp_score

        # Store size (0-100) - based on product count
        if product_count > 500:
            store_score = 90
        elif product_count > 200:
            store_score = 75
        elif product_count > 100:
            store_score = 60
        elif product_count > 50:
            store_score = 45
        elif product_count > 20:
            store_score = 30
        else:
            store_score = 15
        result.store_size = store_score
        breakdown["store_size"] = store_score

        # Product count score (0-100)
        result.product_count_score = min(100, product_count / 5)
        breakdown["product_count"] = result.product_count_score

        # Growth signals (0-100) - newer companies = more growth
        growth_score = 50.0
        if founded_year > 2020:
            growth_score = 80
        elif founded_year > 2018:
            growth_score = 65
        elif founded_year > 2015:
            growth_score = 50
        elif founded_year > 2010:
            growth_score = 40
        if city in ["Mumbai", "Delhi", "Bangalore", "Bengaluru", "Gurgaon", "Pune"]:
            growth_score = min(100, growth_score + 10)
        result.growth_signals = growth_score
        breakdown["growth_signals"] = growth_score

        # Social activity (0-100)
        social_score = 20.0
        if instagram_followers > 100000:
            social_score = 90
        elif instagram_followers > 50000:
            social_score = 75
        elif instagram_followers > 10000:
            social_score = 60
        elif instagram_followers > 5000:
            social_score = 45
        elif instagram_url:
            social_score = 30
        if facebook_likes > 50000:
            social_score = min(100, social_score + 15)
        result.social_activity = social_score
        breakdown["social_activity"] = social_score

        # Chatbot gap (0-100) - higher = bigger gap = more opportunity
        chatbot_gap_score = 90.0 if not has_chatbot else 20.0
        if has_chatbot and chatbot_tool.lower() in ["tidio", "crisp", "livechat"]:
            chatbot_gap_score = 50  # Can upgrade
        result.chatbot_gap = chatbot_gap_score
        breakdown["chatbot_gap"] = chatbot_gap_score

        # FAQ size (0-100) - estimated from description length
        faq_score = 30.0
        if len(description) > 500:
            faq_score = 60
        elif len(description) > 200:
            faq_score = 45
        result.faq_size = faq_score
        breakdown["faq_size"] = faq_score

        # Calculate weighted total
        total = 0.0
        for component, weight in self.WEIGHTS.items():
            component_key = component if component != "product_count" else "product_count_score"
            component_value = getattr(result, component_key, 0)
            total += component_value * weight

        result.total_score = round(min(100, total), 1)
        result.score_breakdown = breakdown

        # Classification
        if result.total_score >= 70:
            result.classification = "hot"
        elif result.total_score >= 50:
            result.classification = "warm"
        else:
            result.classification = "cold"

        # Confidence based on data completeness
        data_points = sum([
            1 if platform else 0,
            1 if product_count > 0 else 0,
            1 if instagram_url or facebook_url else 0,
            1 if category else 0,
            1 if city else 0,
        ])
        result.confidence = min(1.0, data_points / 4)

        return result
