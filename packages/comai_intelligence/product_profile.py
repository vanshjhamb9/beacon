"""COMAI Product Intelligence Profile.

Embeds complete COMAI product knowledge into every engine.
Beacon must permanently understand what COMAI does, who buys it, and why.

COMAI is NOT a chatbot. COMAI is an AI Revenue Platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class COMAIProduct:
    """Single COMAI product/capability."""

    name: str
    category: str
    description: str
    target_pains: tuple[str, ...]
    target_industries: tuple[str, ...]
    target_platforms: tuple[str, ...]
    min_revenue_inr: int
    max_revenue_inr: int
    min_employees: int
    max_employees: int
    avg_deal_size_inr: int
    sales_cycle_days: int
    key_metrics: tuple[str, ...]
    competes_with: tuple[str, ...]


@dataclass(frozen=True)
class COMAIMarketKnowledge:
    """Who buys COMAI and why."""

    perfect_customer_description: str
    buyer_personas: tuple[str, ...]
    common_objections: tuple[str, ...]
    success_metrics: tuple[str, ...]
    rejection_reasons: tuple[str, ...]


class COMAIProductCatalog:
    """Complete COMAI product intelligence.

    This is the single source of truth for what COMAI sells,
    who buys it, and how it creates value.
    """

    PRODUCTS: tuple[COMAIProduct, ...] = (
        COMAIProduct(
            name="AI Sales Agent",
            category="sales_automation",
            description="Autonomous AI that converts visitors into buyers 24/7",
            target_pains=(
                "low_conversion_rate",
                "high_cart_abandonment",
                "no_24x7_sales_coverage",
                "manual_sales_process",
                "poor_product_discovery",
            ),
            target_industries=(
                "beauty", "cosmetics", "skincare", "fashion", "apparel",
                "jewellery", "home_decor", "furniture", "luxury_d2c",
                "electronics_accessories", "health_wellness", "supplements",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=2_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=10,
            max_employees=250,
            avg_deal_size_inr=3_60_000,
            sales_cycle_days=45,
            key_metrics=("conversion_rate", "revenue_per_visitor", "cart_recovery_rate"),
            competes_with=("gorgias", "tidio", "intercom", "drift", "zendesk"),
        ),
        COMAIProduct(
            name="AI Customer Support",
            category="support_automation",
            description="AI that resolves 80%+ of customer queries instantly",
            target_pains=(
                "support_overload",
                "slow_response_time",
                "high_support_costs",
                "poor_faq_coverage",
                "manual_ticket_handling",
                "long_resolution_time",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "baby_products", "pet_products", "organic_food", "electronics_accessories",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=2_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=10,
            max_employees=250,
            avg_deal_size_inr=2_40_000,
            sales_cycle_days=30,
            key_metrics=("support_ticket_reduction", "response_time", "csat_score"),
            competes_with=("zendesk", "freshdesk", "intercom", "gorgias", "helpscout"),
        ),
        COMAIProduct(
            name="AI Shopping Assistant",
            category="sales_automation",
            description="Conversational AI that guides shoppers to the right products",
            target_pains=(
                "poor_product_discovery",
                "large_catalog_overwhelm",
                "low_conversion_rate",
                "no_personalization",
                "high_bounce_rate",
            ),
            target_industries=(
                "beauty", "cosmetics", "skincare", "fashion", "apparel",
                "jewellery", "home_decor", "furniture", "luxury_d2c",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=5_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=15,
            max_employees=250,
            avg_deal_size_inr=3_60_000,
            sales_cycle_days=45,
            key_metrics=("product_discovery_rate", "avg_order_value", "conversion_rate"),
            competes_with=("nodalify", "limechat", "manychat"),
        ),
        COMAIProduct(
            name="WhatsApp AI Automation",
            category="communication_automation",
            description="AI-powered WhatsApp for sales, support, and marketing",
            target_pains=(
                "heavy_whatsapp_dependence",
                "manual_whatsapp_responses",
                "no_broadcast_automation",
                "poor_customer_reengagement",
                "slow_order_updates",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "baby_products", "pet_products", "organic_food", "health_wellness",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=2_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=10,
            max_employees=250,
            avg_deal_size_inr=2_40_000,
            sales_cycle_days=30,
            key_metrics=("whatsapp_response_time", "broadcast_open_rate", "recovery_rate"),
            competes_with=("wati", "aisensy", "interakt", "whatsapp_business_api"),
        ),
        COMAIProduct(
            name="AI Product Recommendation",
            category="personalization",
            description="AI that shows every customer exactly what they want to buy",
            target_pains=(
                "no_personalization",
                "generic_product_pages",
                "low_avg_order_value",
                "poor_cross_sell",
                "no_upsell",
                "large_catalog",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "furniture", "luxury_d2c", "electronics_accessories",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=5_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=15,
            max_employees=250,
            avg_deal_size_inr=3_60_000,
            sales_cycle_days=45,
            key_metrics=("avg_order_value", "cross_sell_rate", "product_click_rate"),
            competes_with=("recombee", "dynamic_yield", "barilliance"),
        ),
        COMAIProduct(
            name="AI Upselling & Cross-selling",
            category="revenue_optimization",
            description="AI that maximizes cart value through smart recommendations",
            target_pains=(
                "low_avg_order_value",
                "no_upsell",
                "no_cross_sell",
                "missed_revenue_per_order",
                "poor_bundle_strategy",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "baby_products", "health_wellness", "supplements",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=5_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=15,
            max_employees=250,
            avg_deal_size_inr=2_40_000,
            sales_cycle_days=30,
            key_metrics=("avg_order_value", "upsell_accept_rate", "revenue_per_order"),
            competes_with=("rebuy", "bold", "in_cart"),
        ),
        COMAIProduct(
            name="Cart Recovery",
            category="conversion_optimization",
            description="AI-powered abandoned cart recovery across email, WhatsApp, SMS",
            target_pains=(
                "high_cart_abandonment",
                "lost_revenue_from_abandonment",
                "manual_cart_followup",
                "poor_recovery_rate",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "furniture", "baby_products", "health_wellness",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=2_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=10,
            max_employees=250,
            avg_deal_size_inr=2_40_000,
            sales_cycle_days=30,
            key_metrics=("cart_recovery_rate", "recovered_revenue", "recovery_time"),
            competes_with=("recart", "omnisend", "klaviyo"),
        ),
        COMAIProduct(
            name="Order Tracking",
            category="operations",
            description="AI-powered branded order tracking that drives repeat purchases",
            target_pains=(
                "manual_order_tracking",
                "wwhere_is_my_order_queries",
                "poor_post_purchase_experience",
                "low_repeat_purchase_rate",
            ),
            target_industries=(
                "fashion", "apparel", "home_decor", "baby_products",
                "pet_products", "organic_food", "electronics_accessories",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=2_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=10,
            max_employees=250,
            avg_deal_size_inr=1_20_000,
            sales_cycle_days=21,
            key_metrics=("wismo_reduction", "repeat_purchase_rate", "tracking_page_views"),
            competes_with=("aftership", "parcelpanel", "tracktor"),
        ),
        COMAIProduct(
            name="Customer Personalization",
            category="personalization",
            description="AI that personalizes every touchpoint — homepage to post-purchase",
            target_pains=(
                "no_personalization",
                "generic_experience",
                "low_repeat_purchase_rate",
                "poor_customer_retention",
                "no_customer_segmentation",
            ),
            target_industries=(
                "beauty", "cosmetics", "skincare", "fashion", "apparel",
                "jewellery", "luxury_d2c", "health_wellness",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=10_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=20,
            max_employees=250,
            avg_deal_size_inr=3_60_000,
            sales_cycle_days=45,
            key_metrics=("repeat_purchase_rate", "customer_lifetime_value", "engagement_rate"),
            competes_with=("optimizely", "Dynamic Yield", "monetate"),
        ),
        COMAIProduct(
            name="Marketing Automation",
            category="marketing",
            description="AI-driven marketing automation across email, WhatsApp, SMS",
            target_pains=(
                "manual_marketing",
                "poor_email_engagement",
                "no_broadcast_automation",
                "poor_customer_reengagement",
                "no_drip_campaigns",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "baby_products", "health_wellness", "supplements",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=5_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=15,
            max_employees=250,
            avg_deal_size_inr=2_40_000,
            sales_cycle_days=30,
            key_metrics=("email_open_rate", "broadcast_roi", "customer_reactivation_rate"),
            competes_with=("klaviyo", "mailchimp", "omnisend", "drip"),
        ),
        COMAIProduct(
            name="Ecommerce AI Copilot",
            category="operations",
            description="AI copilot for ecommerce founders — analytics, insights, actions",
            target_pains=(
                "data_silos",
                "manual_reporting",
                "slow_decision_making",
                "no_ai_insights",
                "operational_complexity",
            ),
            target_industries=(
                "beauty", "fashion", "apparel", "jewellery", "home_decor",
                "luxury_d2c", "electronics_accessories", "health_wellness",
            ),
            target_platforms=("shopify", "shopify_plus", "woocommerce", "magento"),
            min_revenue_inr=10_00_00_000,
            max_revenue_inr=250_00_00_000,
            min_employees=20,
            max_employees=250,
            avg_deal_size_inr=4_80_000,
            sales_cycle_days=60,
            key_metrics=("decision_speed", "insight_accuracy", "operational_efficiency"),
            competes_with=("triple_a", "glew", "lifetimely"),
        ),
    )

    MARKET_KNOWLEDGE = COMAIMarketKnowledge(
        perfect_customer_description=(
            "Growing Indian D2C ecommerce brand doing ₹2-250 Cr revenue, "
            "10-250 employees, on Shopify/WooCommerce/Magento, selling beauty, "
            "fashion, jewellery, home decor, or health products, with active "
            "customer support needs, running Meta/Google Ads, using WhatsApp, "
            "and growing fast enough to need AI automation."
        ),
        buyer_personas=(
            "Founder/CEO — cares about revenue growth and operational efficiency",
            "Head of Ecommerce — cares about conversion rate and AOV",
            "Marketing Head — cares about customer acquisition cost and retention",
            "CX Head — cares about support quality and cost reduction",
            "Growth Head — cares about scaling without linear cost increase",
            "Operations Head — cares about automation and process efficiency",
        ),
        common_objections=(
            "We already have a chatbot",
            "We are too small for AI",
            "Our team can handle support",
            "We use Klaviyo for automation",
            "Our budget is tight",
            "We want to try building in-house",
            "We need to see ROI proof first",
        ),
        success_metrics=(
            "30% reduction in support costs",
            "20% increase in conversion rate",
            "15% increase in average order value",
            "40% faster response time",
            "25% increase in repeat purchases",
            "60% reduction in manual operations",
        ),
        rejection_reasons=(
            "Enterprise with custom ERP/SAP",
            "Marketplace-only seller (Amazon/Flipkart without own website)",
            "B2B manufacturer without D2C",
            "Government/public sector",
            "Hospital/bank/insurance/university",
            "Agency or consultancy",
            "SaaS company",
            "Below ₹2 Cr revenue",
            "Above 5000 employees",
            "No ecommerce checkout on website",
        ),
    )

    # Industry pain multipliers — industries with higher pain get higher scores
    INDUSTRY_PAIN_MULTIPLIER: dict[str, float] = {
        "beauty": 1.0,
        "cosmetics": 1.0,
        "skincare": 1.0,
        "fashion": 0.95,
        "apparel": 0.95,
        "jewellery": 0.9,
        "home_decor": 0.85,
        "furniture": 0.8,
        "baby_products": 0.9,
        "pet_products": 0.8,
        "organic_food": 0.85,
        "luxury_d2c": 0.95,
        "electronics_accessories": 0.85,
        "health_wellness": 0.9,
        "supplements": 0.9,
    }

    @classmethod
    def get_products_for_pain(cls, pain_type: str) -> list[COMAIProduct]:
        """Return all COMAI products that address a specific pain."""
        return [p for p in cls.PRODUCTS if pain_type in p.target_pains]

    @classmethod
    def get_products_for_industry(cls, industry: str) -> list[COMAIProduct]:
        """Return all COMAI products relevant to an industry."""
        return [p for p in cls.PRODUCTS if industry in p.target_industries]

    @classmethod
    def get_products_for_platform(cls, platform: str) -> list[COMAIProduct]:
        """Return all COMAI products that work on a platform."""
        return [p for p in cls.PRODUCTS if platform in p.target_platforms]

    @classmethod
    def get_max_deal_size(cls) -> int:
        """Return the maximum possible deal size across all products."""
        return max(p.avg_deal_size_inr for p in cls.PRODUCTS)

    @classmethod
    def get_industry_pain_multiplier(cls, industry: str) -> float:
        """Return pain multiplier for an industry. Higher = more pain = higher priority."""
        return cls.INDUSTRY_PAIN_MULTIPLIER.get(industry, 0.7)

    @classmethod
    def matches_revenue_range(cls, revenue_inr: int) -> bool:
        """Check if revenue falls within any product's target range."""
        return any(p.min_revenue_inr <= revenue_inr <= p.max_revenue_inr for p in cls.PRODUCTS)

    @classmethod
    def matches_employee_range(cls, employees: int) -> bool:
        """Check if employee count falls within any product's target range."""
        return any(p.min_employees <= employees <= p.max_employees for p in cls.PRODUCTS)

    @classmethod
    def applicable_products(
        cls, industry: str, platform: str, revenue_inr: int, employees: int
    ) -> list[COMAIProduct]:
        """Return all COMAI products applicable to a company profile."""
        results = []
        for product in cls.PRODUCTS:
            if (
                industry in product.target_industries
                and platform in product.target_platforms
                and product.min_revenue_inr <= revenue_inr <= product.max_revenue_inr
                and product.min_employees <= employees <= product.max_employees
            ):
                results.append(product)
        return results

    @classmethod
    def estimate_total_arr(cls, products: list[COMAIProduct]) -> int:
        """Estimate total ARR from applicable products."""
        return sum(p.avg_deal_size_inr for p in products)

    @classmethod
    def is_rejection_match(cls, company_text: str) -> str | None:
        """Check if company text matches any rejection reason. Returns reason or None."""
        text_lower = company_text.lower()
        for reason in cls.MARKET_KNOWLEDGE.rejection_reasons:
            if reason.lower() in text_lower:
                return reason
        return None
