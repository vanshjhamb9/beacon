"""Pain Intelligence Engine — Detects and scores pain points COMAI can solve.

Instead of returning "Company + Website + Email", return:
Pain + Growth + Intent + Technology + Automation Maturity + AI Readiness
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.comai_intelligence.product_profile import COMAIProductCatalog


@dataclass
class PainSignal:
    """Single detected pain point."""

    pain_type: str
    description: str
    confidence: float  # 0-1
    evidence: list[str]  # URLs or descriptions proving the pain
    source: str
    comai_products: tuple[str, ...]  # Which COMAI products address this
    severity: str  # "critical", "high", "medium", "low"
    estimated_annual_cost_inr: int = 0  # Cost of this pain to the company

    def to_dict(self) -> dict[str, Any]:
        return {
            "pain_type": self.pain_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "source": self.source,
            "comai_products": self.comai_products,
            "severity": self.severity,
            "estimated_annual_cost_inr": self.estimated_annual_cost_inr,
        }


class PainIntelligenceEngine:
    """Detects and scores pain points that COMAI can solve.

    Maps observable company attributes to specific pain points,
    then recommends which COMAI products address each pain.
    """

    PAIN_DEFINITIONS: dict[str, dict[str, Any]] = {
        "support_overload": {
            "description": "Customer support team is overwhelmed with queries",
            "indicators": {
                "no_chatbot": {"weight": 0.9, "severity": "critical"},
                "large_product_catalog": {"weight": 0.7, "severity": "high"},
                "many_product_pages": {"weight": 0.6, "severity": "medium"},
                "complex_products": {"weight": 0.5, "severity": "medium"},
                "high_traffic_low_automation": {"weight": 0.8, "severity": "high"},
            },
            "comai_products": ("AI Customer Support", "WhatsApp AI Automation"),
            "annual_cost_per_ticket_inr": 50,
        },
        "manual_sales": {
            "description": "Sales process is manual, no AI assistance for conversions",
            "indicators": {
                "no_ai_assistant": {"weight": 0.9, "severity": "critical"},
                "no_shopping_assistant": {"weight": 0.85, "severity": "high"},
                "high_traffic_low_conversion": {"weight": 0.8, "severity": "high"},
                "no_product_recommendations": {"weight": 0.7, "severity": "medium"},
            },
            "comai_products": ("AI Sales Agent", "AI Shopping Assistant"),
            "annual_cost_per_lost_sale_inr": 2000,
        },
        "poor_personalization": {
            "description": "Generic shopping experience, no personalization",
            "indicators": {
                "no_recommendation_engine": {"weight": 0.85, "severity": "high"},
                "generic_product_pages": {"weight": 0.7, "severity": "medium"},
                "no_customer_segmentation": {"weight": 0.6, "severity": "medium"},
                "no_dynamic_content": {"weight": 0.5, "severity": "low"},
            },
            "comai_products": ("AI Product Recommendation", "Customer Personalization"),
            "annual_cost_per_customer_inr": 500,
        },
        "cart_abandonment": {
            "description": "High cart abandonment rate, lost revenue",
            "indicators": {
                "no_cart_recovery": {"weight": 0.9, "severity": "critical"},
                "high_traffic_low_conversion": {"weight": 0.8, "severity": "high"},
                "no_checkout_optimization": {"weight": 0.7, "severity": "high"},
                "no_abandoned_cart_emails": {"weight": 0.85, "severity": "high"},
            },
            "comai_products": ("Cart Recovery", "AI Sales Agent"),
            "annual_cost_per_abandoned_cart_inr": 1500,
        },
        "heavy_whatsapp": {
            "description": "Heavy WhatsApp dependence without automation",
            "indicators": {
                "whatsapp_button_present": {"weight": 0.7, "severity": "medium"},
                "no_ai_whatsapp": {"weight": 0.85, "severity": "high"},
                "manual_response_indicators": {"weight": 0.8, "severity": "high"},
                "whatsapp_broadcast": {"weight": 0.6, "severity": "medium"},
            },
            "comai_products": ("WhatsApp AI Automation", "Marketing Automation"),
            "annual_cost_per_manual_whatsapp_inr": 200,
        },
        "low_avg_order_value": {
            "description": "Missing upsell and cross-sell opportunities",
            "indicators": {
                "no_upsell": {"weight": 0.8, "severity": "high"},
                "no_cross_sell": {"weight": 0.8, "severity": "high"},
                "no_bundle_offers": {"weight": 0.6, "severity": "medium"},
                "no_product_recommendations": {"weight": 0.7, "severity": "medium"},
            },
            "comai_products": ("AI Upselling & Cross-selling", "AI Product Recommendation"),
            "annual_cost_per_order_inr": 300,
        },
        "poor_retention": {
            "description": "Low repeat purchase rate, poor customer retention",
            "indicators": {
                "low_repeat_purchase": {"weight": 0.85, "severity": "high"},
                "no_loyalty_program": {"weight": 0.5, "severity": "medium"},
                "no_post_purchase_engagement": {"weight": 0.7, "severity": "high"},
                "no_reengagement_campaigns": {"weight": 0.6, "severity": "medium"},
            },
            "comai_products": ("Customer Personalization", "Marketing Automation"),
            "annual_cost_per_churned_customer_inr": 3000,
        },
        "manual_operations": {
            "description": "Operations are manual, no AI copilot",
            "indicators": {
                "no_analytics_dashboard": {"weight": 0.6, "severity": "medium"},
                "manual_reporting": {"weight": 0.7, "severity": "high"},
                "no_ai_insights": {"weight": 0.8, "severity": "high"},
                "data_silos": {"weight": 0.5, "severity": "medium"},
            },
            "comai_products": ("Ecommerce AI Copilot", "Marketing Automation"),
            "annual_cost_per_hour_manual_inr": 500,
        },
        "slow_response_time": {
            "description": "Customer queries take too long to resolve",
            "indicators": {
                "no_live_chat": {"weight": 0.7, "severity": "high"},
                "no_ai_support": {"weight": 0.85, "severity": "critical"},
                "email_only_support": {"weight": 0.6, "severity": "medium"},
                "no_self_service": {"weight": 0.5, "severity": "medium"},
            },
            "comai_products": ("AI Customer Support", "WhatsApp AI Automation"),
            "annual_cost_per_slow_response_inr": 100,
        },
        "poor_order_tracking": {
            "description": "Manual order tracking, high WISMO queries",
            "indicators": {
                "no_tracking_page": {"weight": 0.8, "severity": "high"},
                "manual_tracking_updates": {"weight": 0.7, "severity": "high"},
                "high_wismo_queries": {"weight": 0.9, "severity": "critical"},
                "no_branded_tracking": {"weight": 0.6, "severity": "medium"},
            },
            "comai_products": ("Order Tracking", "WhatsApp AI Automation"),
            "annual_cost_per_wismo_query_inr": 30,
        },
    }

    def analyze(
        self, company: dict[str, Any], tech_stack: dict[str, Any] | None = None
    ) -> list[PainSignal]:
        """Analyze a company for pain points COMAI can solve.

        Args:
            company: Company data with observable attributes.
            tech_stack: Detected technology stack.

        Returns:
            List of detected PainSignal objects, sorted by severity.
        """
        tech = tech_stack or {}
        pains: list[PainSignal] = []

        for pain_type, definition in self.PAIN_DEFINITIONS.items():
            indicators = definition["indicators"]
            matched_indicators: list[tuple[str, float, str]] = []
            total_weight = 0.0

            for indicator_name, indicator_config in indicators.items():
                detected, evidence = self._check_indicator(
                    indicator_name, company, tech
                )
                if detected:
                    matched_indicators.append(
                        (indicator_name, indicator_config["weight"], evidence)
                    )
                    total_weight += indicator_config["weight"]

            if matched_indicators:
                # Calculate confidence based on matched indicators
                max_possible = sum(c["weight"] for c in indicators.values())
                confidence = min(total_weight / max_possible, 1.0) if max_possible > 0 else 0.0

                # Determine severity
                max_severity = max(
                    indicators[name]["severity"]
                    for name, _, _ in matched_indicators
                )

                # Calculate estimated annual cost
                annual_cost = self._estimate_annual_cost(
                    pain_type, company, len(matched_indicators)
                )

                # Get applicable COMAI products
                comai_products = definition["comai_products"]

                evidence_urls = [e for _, _, e in matched_indicators if e]

                pains.append(PainSignal(
                    pain_type=pain_type,
                    description=definition["description"],
                    confidence=confidence,
                    evidence=evidence_urls,
                    source="pain_intelligence_engine",
                    comai_products=comai_products,
                    severity=max_severity,
                    estimated_annual_cost_inr=annual_cost,
                ))

        # Sort by severity, then confidence
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        pains.sort(key=lambda p: (severity_order.get(p.severity, 4), -p.confidence))

        return pains

    def _check_indicator(
        self, indicator: str, company: dict[str, Any], tech: dict[str, Any]
    ) -> tuple[bool, str]:
        """Check if a pain indicator is present. Returns (detected, evidence_url)."""

        if indicator == "no_chatbot":
            if not tech.get("chatbot_detected") and not tech.get("ai_chatbot_detected"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_ai_assistant":
            if not tech.get("ai_chatbot_detected") and not tech.get("shopping_assistant"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_shopping_assistant":
            if not tech.get("shopping_assistant"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_recommendation_engine":
            if not tech.get("recommendation_engine"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_cart_recovery":
            if not tech.get("cart_recovery_tool"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_abandoned_cart_emails":
            if not tech.get("cart_recovery_tool") and not tech.get("email_marketing"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_ai_whatsapp":
            if tech.get("whatsapp_detected") and not tech.get("whatsapp_ai"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_upsell":
            if not tech.get("upsell_tool"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_cross_sell":
            if not tech.get("cross_sell_tool"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_tracking_page":
            if not tech.get("tracking_page"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_live_chat":
            if not tech.get("live_chat") and not tech.get("chatbot_detected"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_ai_support":
            if not tech.get("ai_chatbot_detected"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_self_service":
            if not tech.get("knowledge_base") and not tech.get("faq_page"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "whatsapp_button_present":
            if tech.get("whatsapp_detected"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "manual_response_indicators":
            if tech.get("whatsapp_detected") and not tech.get("whatsapp_ai"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "large_product_catalog":
            products = company.get("product_count") or 0
            if products >= 200:
                return True, f"Product count: {products}"
            return False, ""

        if indicator == "many_product_pages":
            products = company.get("product_count") or 0
            if products >= 100:
                return True, f"Product count: {products}"
            return False, ""

        if indicator == "complex_products":
            desc = (company.get("description") or "").lower()
            complex_keywords = ["skincare", "supplements", "health", "nutrition", "ingredients"]
            for kw in complex_keywords:
                if kw in desc:
                    return True, f"Description contains: {kw}"
            return False, ""

        if indicator == "high_traffic_low_automation":
            traffic = company.get("estimated_traffic") or 0
            if traffic >= 50_000 and not tech.get("automation_tool"):
                return True, f"Traffic: {traffic}, no automation detected"
            return False, ""

        if indicator == "high_traffic_low_conversion":
            traffic = company.get("estimated_traffic") or 0
            if traffic >= 30_000:
                return True, f"High traffic ({traffic}) without conversion optimization"
            return False, ""

        if indicator == "no_checkout_optimization":
            if not tech.get("checkout_optimization"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "generic_product_pages":
            if not tech.get("personalization_tool"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_customer_segmentation":
            if not tech.get("crm_detected") and not tech.get("customer_data_platform"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_dynamic_content":
            if not tech.get("personalization_tool"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "no_bundle_offers":
            if not tech.get("bundle_app"):
                return True, company.get("website", "")
            return False, ""

        if indicator == "low_repeat_purchase":
            # Heuristic: if no loyalty/retention tools detected
            if not tech.get("loyalty_program") and not tech.get("retention_tool"):
                return True, "No loyalty or retention tools detected"
            return False, ""

        if indicator == "no_loyalty_program":
            if not tech.get("loyalty_program"):
                return True, "No loyalty program detected"
            return False, ""

        if indicator == "no_post_purchase_engagement":
            if not tech.get("post_purchase_tool"):
                return True, "No post-purchase engagement tool"
            return False, ""

        if indicator == "no_reengagement_campaigns":
            if not tech.get("email_marketing") or not tech.get("retention_tool"):
                return True, "No re-engagement campaigns detected"
            return False, ""

        if indicator == "no_analytics_dashboard":
            if not tech.get("analytics_tool") and not tech.get("ga4"):
                return True, "No analytics dashboard detected"
            return False, ""

        if indicator == "manual_reporting":
            if not tech.get("reporting_tool") and not tech.get("bi_tool"):
                return True, "No reporting/BI tool detected"
            return False, ""

        if indicator == "no_ai_insights":
            if not tech.get("ai_tool") and not tech.get("copilot"):
                return True, "No AI insights tool detected"
            return False, ""

        if indicator == "data_silos":
            if not tech.get("crm_detected") and not tech.get("cdp"):
                return True, "No CDP or integrated CRM"
            return False, ""

        if indicator == "email_only_support":
            has_live = tech.get("live_chat") or tech.get("chatbot_detected")
            has_phone = tech.get("phone_support")
            if not has_live and not has_phone:
                return True, "No live chat or phone support detected"
            return False, ""

        if indicator == "no_tracking_page":
            if not tech.get("tracking_page"):
                return True, "No branded tracking page"
            return False, ""

        if indicator == "manual_tracking_updates":
            if not tech.get("tracking_tool"):
                return True, "No automated tracking tool"
            return False, ""

        if indicator == "high_wismo_queries":
            # Heuristic: ecommerce with no tracking = high WISMO
            if company.get("product_count", 0) >= 50 and not tech.get("tracking_tool"):
                return True, "Ecommerce with no tracking = likely high WISMO"
            return False, ""

        if indicator == "no_branded_tracking":
            if not tech.get("tracking_page"):
                return True, "No branded tracking page"
            return False, ""

        if indicator == "no_product_recommendations":
            if not tech.get("recommendation_engine"):
                return True, "No recommendation engine"
            return False, ""

        return False, ""

    def _estimate_annual_cost(
        self, pain_type: str, company: dict[str, Any], indicator_count: int
    ) -> int:
        """Estimate annual cost of a pain point in INR."""
        definition = self.PAIN_DEFINITIONS.get(pain_type)
        if not definition:
            return 0

        cost_per_unit = definition.get("annual_cost_per_ticket_inr", 0)
        if cost_per_unit == 0:
            cost_per_unit = definition.get("annual_cost_per_lost_sale_inr", 0)
        if cost_per_unit == 0:
            cost_per_unit = definition.get("annual_cost_per_customer_inr", 0)

        # Rough estimation based on company size
        employees = company.get("estimated_employees") or 50
        revenue = company.get("estimated_revenue") or 5_00_00_000

        # Scale factor based on company size
        scale = max(1.0, employees / 50.0) * max(1.0, revenue / 5_00_00_000)

        base_cost = cost_per_unit * indicator_count * int(scale)
        return min(base_cost, 50_00_000)  # Cap at ₹50L

    def score_pain_intensity(self, pains: list[PainSignal]) -> float:
        """Score overall pain intensity 0-100."""
        if not pains:
            return 0.0

        severity_weights = {"critical": 25, "high": 18, "medium": 10, "low": 5}
        total = sum(
            severity_weights.get(p.severity, 5) * p.confidence for p in pains
        )
        return min(total, 100.0)

    def top_pains(self, pains: list[PainSignal], limit: int = 3) -> list[PainSignal]:
        """Return top N pain signals."""
        return pains[:limit]

    def pain_summary(self, pains: list[PainSignal]) -> str:
        """Generate a human-readable pain summary."""
        if not pains:
            return "No significant pain signals detected."
        top = self.top_pains(pains, 3)
        summaries = [f"{p.pain_type.replace('_', ' ')} ({p.severity})" for p in top]
        return f"Key pains: {', '.join(summaries)}"
