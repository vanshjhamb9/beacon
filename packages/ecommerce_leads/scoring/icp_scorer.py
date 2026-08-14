"""ICP (Ideal Customer Profile) scoring for COMAI lead qualification."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from packages.ecommerce_leads.models import EnrichedEcommerceLead

logger = logging.getLogger(__name__)


@dataclass
class ICPScoringResult:
    """Result of ICP scoring with all dimensions."""
    icp_match_score: float = 0.0
    buying_probability: float = 0.0
    growth_score: float = 0.0
    decision_maker_accessibility: float = 0.0
    support_pain_score: float = 0.0
    overall_comai_sales_score: float = 0.0
    icp_breakdown: dict[str, float] = None
    reasons: list[str] = None
    disqualifiers: list[str] = None

    def __post_init__(self):
        if self.icp_breakdown is None:
            self.icp_breakdown = {}
        if self.reasons is None:
            self.reasons = []
        if self.disqualifiers is None:
            self.disqualifiers = []


class ICPScorer:
    """Score leads against COMAI's Ideal Customer Profile.
    
    ICP Criteria:
    - Indian businesses only
    - Shopify or WooCommerce stores
    - Small to mid-sized D2C brands
    - Growing ecommerce businesses
    - 5-100 employees (estimated)
    - Active within the last 12 months
    - Strong Instagram/Facebook presence
    - Uses WhatsApp Business
    - No AI chatbot or advanced customer support automation detected
    - Likely handling customer support manually
    - Founder or decision maker is publicly discoverable
    - Estimated revenue ₹50 lakh-₹50 crore
    - High probability of purchasing SaaS within the next 90 days
    
    Preferred industries:
    - Fashion, Beauty & Skincare, Cosmetics, Jewellery, Home Decor,
      Pet Products, Health & Supplements, Food & Beverage, Footwear,
      Electronics Accessories, Baby Products, Lifestyle
    
    Exclude:
    - Enterprise brands, Unicorns, Listed companies, Companies with 200+ employees,
      Brands already using enterprise support platforms or advanced AI chatbots,
      Marketplaces (Amazon, Flipkart, etc.)
    """

    PREFERRED_INDUSTRIES = {
        "fashion", "beauty", "skincare", "cosmetics", "jewellery", "jewelry",
        "home decor", "home", "pet products", "pets", "health", "supplements",
        "food", "beverage", "footwear", "electronics accessories", "electronics",
        "baby products", "kids", "lifestyle", "grooming", "personal care",
        "organic", "natural", "wellness", "yoga", "fitness",
    }

    EXCLUDED_KEYWORDS = {
        "marketplace", "amazon", "flipkart", "myntra", "meesho",
        "enterprise", "corp", "corporation", "limited", "ltd",
        "public", "listed", "ipo", "unicorn",
    }

    ENTERPRISE_PLATFORMS = {
        "salesforce", "zendesk", "freshdesk enterprise", "intercom enterprise",
        "drift enterprise", "kustomer", "gorgias", "re:amaze",
    }

    def score(self, lead: EnrichedEcommerceLead) -> ICPScoringResult:
        """Calculate all ICP scoring dimensions."""
        result = ICPScoringResult()

        # Calculate individual scores
        result.icp_match_score = self._calculate_icp_match(lead, result)
        result.buying_probability = self._calculate_buying_probability(lead, result)
        result.growth_score = self._calculate_growth_score(lead, result)
        result.decision_maker_accessibility = self._calculate_dm_accessibility(lead, result)
        result.support_pain_score = self._calculate_support_pain(lead, result)

        # Calculate overall COMAI sales score (weighted average)
        result.overall_comai_sales_score = self._calculate_overall_score(result)

        # Store breakdown
        result.icp_breakdown = {
            "icp_match": result.icp_match_score,
            "buying_probability": result.buying_probability,
            "growth_score": result.growth_score,
            "dm_accessibility": result.decision_maker_accessibility,
            "support_pain": result.support_pain_score,
            "overall": result.overall_comai_sales_score,
        }

        return result

    def _calculate_icp_match(self, lead: EnrichedEcommerceLead, result: ICPScoringResult) -> float:
        """Calculate how well the lead matches COMAI's ICP (0-100)."""
        score = 0.0
        breakdown = {}

        # 1. Indian business (required) - 15 points
        if lead.raw.country == "India":
            score += 15.0
            breakdown["indian_business"] = 15.0
        else:
            result.disqualifiers.append("Not an Indian business")
            breakdown["indian_business"] = 0.0
            return 0.0  # Instant disqualification

        # 2. Platform match (Shopify/WooCommerce) - 15 points
        if lead.shopify_detected or lead.woocommerce_detected:
            score += 15.0
            breakdown["platform_match"] = 15.0
        elif lead.raw.platform in ("shopify", "woocommerce"):
            score += 12.0
            breakdown["platform_match"] = 12.0
        elif lead.raw.platform and lead.raw.platform != "unknown":
            score += 5.0
            breakdown["platform_match"] = 5.0
            result.reasons.append(f"Platform {lead.raw.platform} - not ideal but acceptable")
        else:
            result.disqualifiers.append("Unknown platform")
            breakdown["platform_match"] = 0.0

        # 3. D2C brand indicators - 10 points
        d2c_score = self._score_d2c_indicators(lead)
        score += d2c_score
        breakdown["d2c_brand"] = d2c_score

        # 4. Company size (5-100 employees) - 10 points
        size_score = self._score_company_size(lead)
        score += size_score
        breakdown["company_size"] = size_score

        # 5. Industry match - 10 points
        industry_score = self._score_industry(lead)
        score += industry_score
        breakdown["industry_match"] = industry_score

        # 6. Social presence (Instagram/Facebook) - 10 points
        social_score = self._score_social_presence(lead)
        score += social_score
        breakdown["social_presence"] = social_score

        # 7. WhatsApp usage - 10 points
        if lead.whatsapp_detected:
            score += 10.0
            breakdown["whatsapp"] = 10.0
            result.reasons.append("WhatsApp Business detected")
        else:
            breakdown["whatsapp"] = 0.0

        # 8. No AI chatbot (opportunity) - 10 points
        if not lead.chatbot_detected:
            score += 10.0
            breakdown["no_chatbot"] = 10.0
            result.reasons.append("No AI chatbot - strong COMAI opportunity")
        else:
            # Check if it's an enterprise chatbot
            if self._is_enterprise_chatbot(lead):
                result.disqualifiers.append("Using enterprise chatbot platform")
                breakdown["no_chatbot"] = 0.0
            else:
                score += 3.0
                breakdown["no_chatbot"] = 3.0
                result.reasons.append("Has basic chatbot - may need upgrade")

        # 9. Website activity - 10 points
        if lead.raw.product_count and lead.raw.product_count > 0:
            if lead.raw.product_count >= 100:
                score += 10.0
                breakdown["website_activity"] = 10.0
            elif lead.raw.product_count >= 30:
                score += 7.0
                breakdown["website_activity"] = 7.0
            else:
                score += 4.0
                breakdown["website_activity"] = 4.0
        else:
            breakdown["website_activity"] = 0.0

        # 10. Description quality - 10 points
        if lead.raw.description and len(lead.raw.description) > 50:
            score += 10.0
            breakdown["description_quality"] = 10.0
        elif lead.raw.description:
            score += 5.0
            breakdown["description_quality"] = 5.0
        else:
            breakdown["description_quality"] = 0.0

        result.icp_breakdown = breakdown
        return min(100.0, score)

    def _calculate_buying_probability(self, lead: EnrichedEcommerceLead, result: ICPScoringResult) -> float:
        """Calculate probability of purchasing SaaS within 90 days (0-100)."""
        score = 0.0

        # 1. Support pain indicators - 30 points
        pain_score = self._score_support_pain(lead)
        score += pain_score * 0.3  # Scale to 30

        # 2. Growth indicators - 25 points
        growth_score = self._score_growth_indicators(lead)
        score += growth_score * 0.25

        # 3. Technology readiness - 20 points
        if lead.shopify_detected or lead.woocommerce_detected:
            score += 20.0
            result.reasons.append("Technology stack ready for COMAI integration")

        # 4. Contact availability - 15 points
        if lead.email or lead.phone:
            score += 15.0
            result.reasons.append("Contact information available for outreach")

        # 5. Decision maker identified - 10 points
        if lead.founder_name:
            score += 10.0
            result.reasons.append("Decision maker identified")

        return min(100.0, score)

    def _calculate_growth_score(self, lead: EnrichedEcommerceLead, result: ICPScoringResult) -> float:
        """Calculate business growth potential (0-100)."""
        score = 0.0

        # Product catalog size
        if lead.raw.product_count:
            if lead.raw.product_count >= 500:
                score += 30.0
                result.reasons.append("Large product catalog - scaling business")
            elif lead.raw.product_count >= 100:
                score += 25.0
                result.reasons.append("Mid-size product catalog - growth phase")
            elif lead.raw.product_count >= 30:
                score += 15.0
                result.reasons.append("Growing product catalog")
            else:
                score += 5.0

        # Social media presence
        social_count = len(lead.raw.social_links)
        if social_count >= 3:
            score += 25.0
            result.reasons.append("Strong multi-platform social presence")
        elif social_count >= 2:
            score += 15.0
        elif social_count >= 1:
            score += 8.0

        # Platform sophistication
        if lead.shopify_detected:
            score += 20.0  # Shopify indicates growth mindset
        elif lead.woocommerce_detected:
            score += 15.0

        # Industry growth potential
        if lead.raw.industry:
            industry_lower = lead.raw.industry.lower()
            high_growth_industries = {"beauty", "skincare", "fashion", "health", "supplements", "pet products"}
            if any(ind in industry_lower for ind in high_growth_industries):
                score += 15.0
                result.reasons.append(f"High-growth industry: {lead.raw.industry}")

        # Description indicates growth
        if lead.raw.description:
            desc_lower = lead.raw.description.lower()
            growth_keywords = ["growing", "fastest", "leading", "largest", "premium", "d2c", "direct"]
            if any(kw in desc_lower for kw in growth_keywords):
                score += 10.0

        return min(100.0, score)

    def _calculate_dm_accessibility(self, lead: EnrichedEcommerceLead, result: ICPScoringResult) -> float:
        """Calculate how accessible the decision maker is (0-100)."""
        score = 0.0

        # Founder/CEO identified
        if lead.founder_name:
            score += 40.0
            result.reasons.append(f"Founder identified: {lead.founder_name}")

        # Role specified
        if lead.decision_maker_role:
            score += 20.0

        # Email available
        if lead.email:
            score += 20.0
            result.reasons.append("Email contact available")

        # Phone available
        if lead.phone:
            score += 15.0
            result.reasons.append("Phone contact available")

        # LinkedIn profile
        if lead.linkedin_url:
            score += 5.0

        return min(100.0, score)

    def _calculate_support_pain(self, lead: EnrichedEcommerceLead, result: ICPScoringResult) -> float:
        """Calculate customer support pain level (0-100)."""
        score = 0.0

        # No chatbot = high pain
        if not lead.chatbot_detected:
            score += 40.0
            result.reasons.append("No automated customer support")
            result.reasons.append("Likely handling customer queries manually")

        # No WhatsApp automation
        if not lead.whatsapp_detected:
            score += 25.0
            result.reasons.append("WhatsApp not automated - manual handling likely")

        # No CRM
        if not lead.crm_detected:
            score += 15.0
            result.reasons.append("No CRM integration detected")

        # Large product catalog = more support needs
        if lead.raw.product_count and lead.raw.product_count > 100:
            score += 15.0
            result.reasons.append("Large catalog generates high support volume")

        # Active social = more customer interactions
        if len(lead.raw.social_links) >= 2:
            score += 5.0

        return min(100.0, score)

    def _calculate_overall_score(self, result: ICPScoringResult) -> float:
        """Calculate weighted overall COMAI sales score."""
        weights = {
            "icp_match": 0.30,
            "buying_probability": 0.25,
            "growth_score": 0.20,
            "dm_accessibility": 0.10,
            "support_pain": 0.15,
        }

        overall = (
            result.icp_match_score * weights["icp_match"]
            + result.buying_probability * weights["buying_probability"]
            + result.growth_score * weights["growth_score"]
            + result.decision_maker_accessibility * weights["dm_accessibility"]
            + result.support_pain_score * weights["support_pain"]
        )

        return round(overall, 1)

    def _score_d2c_indicators(self, lead: EnrichedEcommerceLead) -> float:
        """Score D2C brand indicators (0-10)."""
        d2c_keywords = [
            "d2c", "direct to consumer", "direct-to-consumer",
            "own brand", "our brand", "private label", "dtc",
        ]
        text = f"{lead.raw.description} {lead.raw.category} {lead.raw.company_name}".lower()

        if any(kw in text for kw in d2c_keywords):
            return 10.0

        # Industry-based D2C scoring
        if lead.raw.industry:
            industry_lower = lead.raw.industry.lower()
            d2c_industries = {"beauty", "skincare", "cosmetics", "fashion", "grooming", "wellness"}
            if any(ind in industry_lower for ind in d2c_industries):
                return 7.0

        return 3.0  # Base score for Indian ecommerce

    def _score_company_size(self, lead: EnrichedEcommerceLead) -> float:
        """Score company size fit (0-10)."""
        # Estimate based on product count and description
        if lead.raw.product_count:
            if lead.raw.product_count >= 1000:
                # Likely enterprise
                return 2.0
            elif lead.raw.product_count >= 200:
                return 8.0  # Sweet spot
            elif lead.raw.product_count >= 50:
                return 10.0  # Ideal size
            elif lead.raw.product_count >= 10:
                return 7.0
            else:
                return 4.0

        # Default for unknown
        return 6.0

    def _score_industry(self, lead: EnrichedEcommerceLead) -> float:
        """Score industry match (0-10)."""
        if not lead.raw.industry:
            return 5.0  # Neutral

        industry_lower = lead.raw.industry.lower()

        # Check for excluded industries
        for keyword in self.EXCLUDED_KEYWORDS:
            if keyword in industry_lower:
                return 0.0

        # Check for preferred industries
        for industry in self.PREFERRED_INDUSTRIES:
            if industry in industry_lower:
                return 10.0

        # Partial match
        if any(word in industry_lower for word in ["store", "shop", "brand", "retail"]):
            return 6.0

        return 4.0

    def _score_social_presence(self, lead: EnrichedEcommerceLead) -> float:
        """Score social media presence (0-10)."""
        platforms = set(lead.raw.social_links.keys())

        # Instagram/Facebook are most important for COMAI
        has_instagram = "instagram" in platforms
        has_facebook = "facebook" in platforms

        if has_instagram and has_facebook:
            return 10.0
        elif has_instagram or has_facebook:
            return 7.0
        elif len(platforms) >= 2:
            return 5.0
        elif len(platforms) >= 1:
            return 3.0

        return 0.0

    def _score_support_pain(self, lead: EnrichedEcommerceLead) -> float:
        """Score support pain level (0-100) for internal use."""
        score = 0.0

        if not lead.chatbot_detected:
            score += 40.0
        if not lead.whatsapp_detected:
            score += 25.0
        if not lead.crm_detected:
            score += 15.0
        if lead.raw.product_count and lead.raw.product_count > 100:
            score += 15.0
        if len(lead.raw.social_links) >= 2:
            score += 5.0

        return min(100.0, score)

    def _score_growth_indicators(self, lead: EnrichedEcommerceLead) -> float:
        """Score growth indicators (0-100)."""
        score = 0.0

        if lead.raw.product_count:
            if lead.raw.product_count >= 500:
                score += 30.0
            elif lead.raw.product_count >= 100:
                score += 25.0
            elif lead.raw.product_count >= 30:
                score += 15.0

        social_count = len(lead.raw.social_links)
        if social_count >= 3:
            score += 25.0
        elif social_count >= 2:
            score += 15.0

        if lead.shopify_detected:
            score += 20.0

        if lead.raw.description:
            desc_lower = lead.raw.description.lower()
            growth_keywords = ["growing", "fastest", "leading", "premium", "d2c"]
            if any(kw in desc_lower for kw in growth_keywords):
                score += 15.0

        return min(100.0, score)

    def _is_enterprise_chatbot(self, lead: EnrichedEcommerceLead) -> bool:
        """Check if using enterprise chatbot platform."""
        # This would need to check actual chatbot service detected
        # For now, assume most detected chatbots are not enterprise
        return False

    def qualifies_for_export(self, result: ICPScoringResult, lead: EnrichedEcommerceLead) -> tuple[bool, list[str]]:
        """Check if lead qualifies for export based on strict criteria."""
        reasons = []

        # ICP Match >= 80
        if result.icp_match_score < 80.0:
            reasons.append(f"ICP match {result.icp_match_score:.0f} < 80")

        # Buying Probability >= 75
        if result.buying_probability < 75.0:
            reasons.append(f"Buying probability {result.buying_probability:.0f} < 75")

        # Valid website
        if not lead.raw.website or not lead.raw.website.startswith("http"):
            reasons.append("No valid website")

        # At least one verified contact
        if not lead.email and not lead.phone:
            reasons.append("No verified contact information")

        # Clear reason why COMAI is a good fit
        if not result.reasons:
            reasons.append("No clear COMAI fit reason identified")

        # Check for disqualifiers
        if result.disqualifiers:
            reasons.append(f"Disqualifiers: {', '.join(result.disqualifiers)}")

        qualifies = len(reasons) == 0
        return qualifies, reasons
