"""ARIE: ICP Intelligence Engine - The Brain.

Nothing is discovered before ICP. This engine manages ICP profiles,
matches companies against ICPs, and generates ICPs from natural language.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ICPMatchResult:
    """Result of matching a company against an ICP profile."""
    company_domain: str
    icp_profile_id: str
    icp_score: float  # 0-100
    match_details: dict = field(default_factory=dict)
    matched_criteria: list = field(default_factory=list)
    unmatched_criteria: list = field(default_factory=list)
    negative_match: bool = False
    negative_reason: str = ""
    confidence: float = 0.0
    classified_as: str = "UNSCORED"  # HOT, WARM, COLD, UNSCORED, REJECTED


@dataclass
class ICPProfileData:
    """ICP profile data structure."""
    id: str = ""
    name: str = ""
    description: str = ""
    industries: list = field(default_factory=list)
    subcategories: list = field(default_factory=list)
    business_models: list = field(default_factory=list)
    countries: list = field(default_factory=list)
    platforms: list = field(default_factory=list)
    required_technologies: list = field(default_factory=list)
    excluded_technologies: list = field(default_factory=list)
    min_revenue: float = 0
    max_revenue: float = 0
    min_employees: int = 0
    max_employees: int = 0
    min_monthly_traffic: int = 0
    max_monthly_traffic: int = 0
    min_monthly_orders: int = 0
    max_monthly_orders: int = 0
    min_avg_order_value: float = 0
    max_avg_order_value: float = 0
    min_store_age_months: int = 0
    min_growth_rate: float = 0
    pain_categories: list = field(default_factory=list)
    intent_signals: list = field(default_factory=list)
    decision_maker_roles: list = field(default_factory=list)
    negative_industries: list = field(default_factory=list)
    negative_platforms: list = field(default_factory=list)
    negative_countries: list = field(default_factory=list)
    negative_keywords: list = field(default_factory=list)
    min_score: float = 50.0
    auto_qualify_score: float = 80.0
    # Scoring weights
    icp_weight: float = 0.15
    technology_weight: float = 0.20
    growth_weight: float = 0.10
    pain_weight: float = 0.15
    intent_weight: float = 0.15
    revenue_weight: float = 0.10
    decision_maker_weight: float = 0.10
    contact_quality_weight: float = 0.05


class ARIEICPEngine:
    """ICP Intelligence Engine - matches companies against ideal customer profiles.
    
    This is the brain of the ARIE system. Nothing is discovered
    before ICP matching.
    """
    
    # Pre-defined ICP templates for common Indian D2C niches
    NICHE_TEMPLATES = {
        "beauty_india": ICPProfileData(
            name="Beauty India",
            industries=["beauty", "cosmetics", "skincare"],
            subcategories=["organic beauty", "ayurveda", "luxury beauty"],
            business_models=["d2c", "marketplace"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=10000,
            min_monthly_orders=100,
            min_avg_order_value=500,
            pain_categories=["support", "marketing", "personalization"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "cmo"],
        ),
        "fashion_india": ICPProfileData(
            name="Fashion India",
            industries=["fashion", "apparel", "footwear"],
            subcategories=["ethnic wear", "western wear", "luxury fashion"],
            business_models=["d2c", "marketplace"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=15000,
            min_monthly_orders=200,
            min_avg_order_value=800,
            pain_categories=["support", "operations", "logistics"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "coo"],
        ),
        "electronics_india": ICPProfileData(
            name="Electronics India",
            industries=["electronics", "gadgets", "accessories"],
            subcategories=["audio", "wearables", "smart home"],
            business_models=["d2c", "marketplace"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=20000,
            min_monthly_orders=300,
            min_avg_order_value=1000,
            pain_categories=["support", "returns", "warranty"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "cto"],
        ),
        "home_decor_india": ICPProfileData(
            name="Home Decor India",
            industries=["home decor", "furniture", "kitchen"],
            subcategories=["home improvement", "garden", "bedding"],
            business_models=["d2c", "marketplace"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=10000,
            min_monthly_orders=100,
            min_avg_order_value=1500,
            pain_categories=["support", "logistics", "installations"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "coo"],
        ),
        "organic_food_india": ICPProfileData(
            name="Organic Food India",
            industries=["organic food", "health food", "supplements"],
            subcategories=["ayurveda", "tea", "coffee", "snacks"],
            business_models=["d2c", "subscription"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=8000,
            min_monthly_orders=150,
            min_avg_order_value=600,
            pain_categories=["support", "subscriptions", "recurring"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "cmo"],
        ),
        "kids_baby_india": ICPProfileData(
            name="Kids & Baby India",
            industries=["kids", "baby", "maternity"],
            subcategories=["toys", "clothing", "feeding"],
            business_models=["d2c", "marketplace"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=12000,
            min_monthly_orders=200,
            min_avg_order_value=700,
            pain_categories=["support", "safety", "trust"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "cmo"],
        ),
        "pet_products_india": ICPProfileData(
            name="Pet Products India",
            industries=["pet", "pet care", "pet food"],
            subcategories=["dog food", "cat food", "accessories"],
            business_models=["d2c", "subscription"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=5000,
            min_monthly_orders=100,
            min_avg_order_value=500,
            pain_categories=["support", "subscriptions", "loyalty"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo"],
        ),
        "luxury_jewelry_india": ICPProfileData(
            name="Luxury Jewelry India",
            industries=["jewelry", "luxury", "fashion accessories"],
            subcategories=["fine jewelry", "imitation jewelry", "bridal"],
            business_models=["d2c", "marketplace"],
            countries=["India"],
            platforms=["shopify"],
            min_monthly_traffic=10000,
            min_monthly_orders=50,
            min_avg_order_value=3000,
            pain_categories=["support", "trust", "premium experience"],
            intent_signals=["technology_migration", "hiring"],
            decision_maker_roles=["founder", "ceo", "cmo"],
        ),
    }
    
    def __init__(self):
        self.profiles: dict[str, ICPProfileData] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default ICP templates."""
        for key, template in self.NICHE_TEMPLATES.items():
            template.id = f"template_{key}"
            self.profiles[template.id] = template
    
    def create_icp_from_natural_language(self, description: str) -> ICPProfileData:
        """Generate an ICP profile from natural language description.
        
        Example:
            "I sell AI WhatsApp automation for beauty brands in India"
            
        Returns:
            Generated ICPProfileData with all criteria extracted
        """
        icp = ICPProfileData()
        desc_lower = description.lower()
        
        # Extract industry keywords
        industry_keywords = {
            "beauty": ["beauty", "cosmetics", "skincare", "makeup"],
            "fashion": ["fashion", "apparel", "clothing", "wear"],
            "electronics": ["electronics", "gadgets", "tech", "devices"],
            "home decor": ["home decor", "furniture", "home improvement"],
            "food": ["food", "organic", "tea", "coffee", "snacks"],
            "health": ["health", "wellness", "ayurveda", "supplements"],
            "kids": ["kids", "baby", "children", "maternity"],
            "pet": ["pet", "dog", "cat", "animal"],
            "luxury": ["luxury", "premium", "high-end", "exclusive"],
            "jewelry": ["jewelry", "jewellery", "accessories"],
        }
        
        for industry, keywords in industry_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                icp.industries.append(industry)
        
        # Extract country
        country_keywords = {
            "India": ["india", "indian", "delhi", "mumbai", "bangalore"],
            "UAE": ["uae", "dubai", "abu dhabi", "emirates"],
            "USA": ["usa", "united states", "america", "american"],
            "UK": ["uk", "united kingdom", "britain", "british"],
        }
        
        for country, keywords in country_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                icp.countries.append(country)
        
        # Extract platform
        platform_keywords = {
            "shopify": ["shopify", "shop"],
            "woocommerce": ["woocommerce", "wordpress", "woo"],
            "magento": ["magento"],
        }
        
        for platform, keywords in platform_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                icp.platforms.append(platform)
        
        # Extract solution type and map to pain/intent
        solution_keywords = {
            "whatsapp": ["whatsapp", "messaging", "chat"],
            "ai": ["ai", "artificial intelligence", "machine learning", "automation"],
            "chatbot": ["chatbot", "chat bot", "conversational"],
            "crm": ["crm", "customer relationship"],
            "marketing": ["marketing", "email", "campaign"],
        }
        
        for solution, keywords in solution_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                if solution in ["whatsapp", "chatbot"]:
                    icp.pain_categories.extend(["support", "customer_service"])
                    icp.intent_signals.extend(["technology_migration", "automation_initiative"])
                elif solution == "ai":
                    icp.pain_categories.extend(["personalization", "recommendations"])
                    icp.intent_signals.extend(["ai_adoption", "technology_migration"])
                elif solution == "crm":
                    icp.pain_categories.extend(["customer_management", "data_silos"])
                    icp.intent_signals.extend(["crm_migration", "technology_upgrade"])
                elif solution == "marketing":
                    icp.pain_categories.extend(["marketing", "campaign_management"])
                    icp.intent_signals.extend(["marketing_automation", "technology_upgrade"])
        
        # Default values if nothing extracted
        if not icp.industries:
            icp.industries = ["d2c", "ecommerce"]
        if not icp.countries:
            icp.countries = ["India"]
        if not icp.platforms:
            icp.platforms = ["shopify"]
        
        # Set reasonable defaults
        icp.name = f"AI Generated: {description[:50]}"
        icp.description = description
        icp.business_models = ["d2c", "b2c"]
        icp.min_monthly_traffic = 5000
        icp.min_monthly_orders = 50
        icp.min_avg_order_value = 300
        icp.decision_maker_roles = ["founder", "ceo", "cmo", "cto"]
        
        # Deduplicate
        icp.industries = list(set(icp.industries))
        icp.pain_categories = list(set(icp.pain_categories))
        icp.intent_signals = list(set(icp.intent_signals))
        
        return icp
    
    def match_company_against_icp(
        self,
        company_data: dict[str, Any],
        icp: ICPProfileData
    ) -> ICPMatchResult:
        """Match a company against an ICP profile.
        
        Args:
            company_data: Company information dict with keys like:
                domain, industry, country, platform, traffic, orders, etc.
            icp: ICP profile to match against
            
        Returns:
            ICPMatchResult with score and details
        """
        result = ICPMatchResult(
            company_domain=company_data.get("domain", ""),
            icp_profile_id=icp.id,
            icp_score=0.0,
        )
        
        scores = []
        weights = []
        
        # 1. Negative ICP check (instant reject)
        negative_result = self._check_negative_icp(company_data, icp)
        if negative_result["rejected"]:
            result.negative_match = True
            result.negative_reason = negative_result["reason"]
            result.classified_as = "REJECTED"
            result.icp_score = 0.0
            result.confidence = 1.0
            return result
        
        # 2. Industry match (weight: 15%)
        industry_score = self._match_industry(company_data, icp)
        scores.append(industry_score)
        weights.append(icp.icp_weight)
        if industry_score > 50:
            result.matched_criteria.append("industry")
        else:
            result.unmatched_criteria.append("industry")
        
        # 3. Technology fit (weight: 20%)
        tech_score = self._match_technology(company_data, icp)
        scores.append(tech_score)
        weights.append(icp.technology_weight)
        if tech_score > 50:
            result.matched_criteria.append("technology")
        else:
            result.unmatched_criteria.append("technology")
        
        # 4. Growth signals (weight: 10%)
        growth_score = self._match_growth(company_data, icp)
        scores.append(growth_score)
        weights.append(icp.growth_weight)
        if growth_score > 50:
            result.matched_criteria.append("growth")
        else:
            result.unmatched_criteria.append("growth")
        
        # 5. Pain signals (weight: 15%)
        pain_score = self._match_pain(company_data, icp)
        scores.append(pain_score)
        weights.append(icp.pain_weight)
        if pain_score > 50:
            result.matched_criteria.append("pain")
        else:
            result.unmatched_criteria.append("pain")
        
        # 6. Buying intent (weight: 15%)
        intent_score = self._match_intent(company_data, icp)
        scores.append(intent_score)
        weights.append(icp.intent_weight)
        if intent_score > 50:
            result.matched_criteria.append("intent")
        else:
            result.unmatched_criteria.append("intent")
        
        # 7. Revenue fit (weight: 10%)
        revenue_score = self._match_revenue(company_data, icp)
        scores.append(revenue_score)
        weights.append(icp.revenue_weight)
        if revenue_score > 50:
            result.matched_criteria.append("revenue")
        else:
            result.unmatched_criteria.append("revenue")
        
        # 8. Decision maker access (weight: 10%)
        dm_score = self._match_decision_maker(company_data, icp)
        scores.append(dm_score)
        weights.append(icp.decision_maker_weight)
        if dm_score > 50:
            result.matched_criteria.append("decision_maker")
        else:
            result.unmatched_criteria.append("decision_maker")
        
        # 9. Contact quality (weight: 5%)
        contact_score = self._match_contact_quality(company_data, icp)
        scores.append(contact_score)
        weights.append(icp.contact_quality_weight)
        if contact_score > 50:
            result.matched_criteria.append("contact_quality")
        else:
            result.unmatched_criteria.append("contact_quality")
        
        # Calculate weighted average
        if weights:
            total_weight = sum(weights)
            result.icp_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            result.icp_score = 0.0
        
        # Calculate confidence
        result.confidence = self._calculate_confidence(company_data, len(result.matched_criteria))
        
        # Classify
        if result.icp_score >= icp.auto_qualify_score:
            result.classified_as = "HOT"
        elif result.icp_score >= icp.min_score:
            result.classified_as = "WARM"
        elif result.icp_score >= 30:
            result.classified_as = "COLD"
        else:
            result.classified_as = "UNSCORED"
        
        # Store match details
        result.match_details = {
            "industry_score": industry_score,
            "technology_score": tech_score,
            "growth_score": growth_score,
            "pain_score": pain_score,
            "intent_score": intent_score,
            "revenue_score": revenue_score,
            "decision_maker_score": dm_score,
            "contact_quality_score": contact_score,
            "weights": {
                "industry": icp.icp_weight,
                "technology": icp.technology_weight,
                "growth": icp.growth_weight,
                "pain": icp.pain_weight,
                "intent": icp.intent_weight,
                "revenue": icp.revenue_weight,
                "decision_maker": icp.decision_maker_weight,
                "contact_quality": icp.contact_quality_weight,
            }
        }
        
        return result
    
    def _check_negative_icp(self, company: dict, icp: ICPProfileData) -> dict:
        """Check if company matches any negative ICP criteria."""
        domain = company.get("domain", "").lower()
        industry = company.get("industry", "").lower()
        country = company.get("country", "").lower()
        platform = company.get("platform", "").lower()
        
        # Check negative industries
        for neg_industry in icp.negative_industries:
            if neg_industry.lower() in industry:
                return {"rejected": True, "reason": f"Negative industry: {neg_industry}"}
        
        # Check negative platforms
        for neg_platform in icp.negative_platforms:
            if neg_platform.lower() in platform:
                return {"rejected": True, "reason": f"Negative platform: {neg_platform}"}
        
        # Check negative countries
        for neg_country in icp.negative_countries:
            if neg_country.lower() in country:
                return {"rejected": True, "reason": f"Negative country: {neg_country}"}
        
        # Check negative keywords
        for keyword in icp.negative_keywords:
            if keyword.lower() in domain:
                return {"rejected": True, "reason": f"Negative keyword: {keyword}"}
        
        # Check enterprise signals
        traffic = company.get("traffic", 0)
        employees = company.get("employees", 0)
        if traffic > 1000000 or employees > 1000:
            return {"rejected": True, "reason": "Enterprise company (high traffic/employees)"}
        
        return {"rejected": False, "reason": ""}
    
    def _match_industry(self, company: dict, icp: ICPProfileData) -> float:
        """Match company industry against ICP."""
        company_industry = company.get("industry", "").lower()
        company_category = company.get("category", "").lower()
        company_subcategory = company.get("subcategory", "").lower()
        
        # Exact industry match
        for icp_industry in icp.industries:
            if icp_industry.lower() in company_industry:
                return 100.0
            if icp_industry.lower() in company_category:
                return 90.0
        
        # Subcategory match
        for icp_sub in icp.subcategories:
            if icp_sub.lower() in company_subcategory:
                return 80.0
            if icp_sub.lower() in company_category:
                return 70.0
        
        # Partial match
        for icp_industry in icp.industries:
            if any(word in company_industry for word in icp_industry.split()):
                return 50.0
        
        return 0.0
    
    def _match_technology(self, company: dict, icp: ICPProfileData) -> float:
        """Match company technology stack against ICP."""
        company_platform = company.get("platform", "").lower()
        company_tech = company.get("technology_stack", {})
        
        score = 0.0
        
        # Platform match
        for icp_platform in icp.platforms:
            if icp_platform.lower() in company_platform:
                score += 40.0
                break
        
        # Required technologies
        for req_tech in icp.required_technologies:
            if req_tech.lower() in str(company_tech).lower():
                score += 20.0
        
        # Excluded technologies (penalty)
        for exc_tech in icp.excluded_technologies:
            if exc_tech.lower() in str(company_tech).lower():
                score -= 30.0
        
        return max(0.0, min(100.0, score))
    
    def _match_growth(self, company: dict, icp: ICPProfileData) -> float:
        """Match company growth signals against ICP."""
        traffic_growth = company.get("traffic_growth_rate", 0)
        review_growth = company.get("review_growth_rate", 0)
        growth_rate = company.get("growth_rate", 0)
        
        score = 0.0
        
        if traffic_growth >= icp.min_growth_rate:
            score += 30.0
        if review_growth >= icp.min_growth_rate:
            score += 30.0
        if growth_rate >= icp.min_growth_rate:
            score += 40.0
        
        return min(100.0, score)
    
    def _match_pain(self, company: dict, icp: ICPProfileData) -> float:
        """Match company pain signals against ICP."""
        company_pains = company.get("pain_categories", [])
        
        if not icp.pain_categories:
            return 50.0  # Neutral if no pain criteria
        
        matches = 0
        for pain in company_pains:
            if pain.lower() in [p.lower() for p in icp.pain_categories]:
                matches += 1
        
        if matches == 0:
            return 20.0
        
        return min(100.0, (matches / len(icp.pain_categories)) * 100)
    
    def _match_intent(self, company: dict, icp: ICPProfileData) -> float:
        """Match company buying intent against ICP."""
        company_intent = company.get("intent_signals", [])
        
        if not icp.intent_signals:
            return 50.0  # Neutral if no intent criteria
        
        matches = 0
        for intent in company_intent:
            if intent.lower() in [i.lower() for i in icp.intent_signals]:
                matches += 1
        
        if matches == 0:
            return 20.0
        
        return min(100.0, (matches / len(icp.intent_signals)) * 100)
    
    def _match_revenue(self, company: dict, icp: ICPProfileData) -> float:
        """Match company revenue/AOV against ICP."""
        revenue = company.get("revenue_estimate", 0)
        aov = company.get("avg_order_value", 0)
        traffic = company.get("monthly_traffic", 0)
        orders = company.get("monthly_orders", 0)
        
        score = 0.0
        
        # Revenue range
        if icp.min_revenue and revenue >= icp.min_revenue:
            score += 25.0
        if icp.max_revenue and revenue <= icp.max_revenue:
            score += 25.0
        
        # AOV range
        if icp.min_avg_order_value and aov >= icp.min_avg_order_value:
            score += 25.0
        if icp.max_avg_order_value and aov <= icp.max_avg_order_value:
            score += 25.0
        
        # Traffic range (if no revenue data)
        if revenue == 0:
            if icp.min_monthly_traffic and traffic >= icp.min_monthly_traffic:
                score += 50.0
        
        # Orders range (if no revenue data)
        if revenue == 0:
            if icp.min_monthly_orders and orders >= icp.min_monthly_orders:
                score += 50.0
        
        return min(100.0, score)
    
    def _match_decision_maker(self, company: dict, icp: ICPProfileData) -> float:
        """Match company decision maker access against ICP."""
        company_dms = company.get("decision_makers", [])
        
        if not icp.decision_maker_roles:
            return 50.0
        
        if not company_dms:
            return 10.0
        
        matches = 0
        for dm in company_dms:
            dm_role = dm.get("role", "").lower()
            for icp_role in icp.decision_maker_roles:
                if icp_role.lower() in dm_role:
                    matches += 1
                    break
        
        if matches == 0:
            return 20.0
        
        return min(100.0, (matches / len(icp.decision_maker_roles)) * 100)
    
    def _match_contact_quality(self, company: dict, icp: ICPProfileData) -> float:
        """Match company contact quality against ICP."""
        has_email = bool(company.get("email"))
        has_phone = bool(company.get("phone"))
        has_linkedin = bool(company.get("linkedin_url"))
        has_dm = bool(company.get("decision_makers"))
        
        score = 0.0
        if has_email:
            score += 30.0
        if has_phone:
            score += 30.0
        if has_linkedin:
            score += 20.0
        if has_dm:
            score += 20.0
        
        return score
    
    def _calculate_confidence(self, company: dict, matched_count: int) -> float:
        """Calculate confidence score based on data availability."""
        data_points = [
            bool(company.get("domain")),
            bool(company.get("industry")),
            bool(company.get("country")),
            bool(company.get("platform")),
            bool(company.get("traffic")),
            bool(company.get("revenue_estimate")),
            bool(company.get("email")),
            bool(company.get("phone")),
            bool(company.get("decision_makers")),
        ]
        
        available = sum(1 for p in data_points if p)
        total = len(data_points)
        
        base_confidence = (available / total) * 100
        
        # Boost for matched criteria
        match_boost = matched_count * 5
        
        return min(100.0, base_confidence + match_boost)
