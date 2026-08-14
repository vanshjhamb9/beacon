"""Pain point detection engine - deterministic, no LLM.

Analyzes technology stack, support tools, and business signals
to identify sales opportunities for COMAI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PainPoint:
    """A detected pain point with evidence."""
    category: str
    description: str
    severity: str  # high, medium, low
    comai_solution: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


@dataclass
class PainAnalysis:
    """Complete pain point analysis for a company."""
    pain_points: list[PainPoint] = field(default_factory=list)
    total_pain_score: float = 0.0
    top_pain: str = ""
    recommended_module: str = ""
    business_value: str = ""


class PainPointDetector:
    """Detect pain points from scraped technology and business data."""

    def analyze(
        self,
        *,
        has_chatbot: bool = False,
        chatbot_tool: str = "",
        has_whatsapp_widget: bool = False,
        has_live_chat: bool = False,
        has_crm: bool = False,
        support_tools: list[str] | None = None,
        platform: str = "",
        product_count: int = 0,
        has_ecommerce: bool = True,
        category: str = "",
        instagram_url: str = "",
        facebook_url: str = "",
        phone: str = "",
        email: str = "",
        description: str = "",
    ) -> PainAnalysis:
        """Analyze pain points from available data."""
        pain_points: list[PainPoint] = []
        support_tools = support_tools or []

        # No chatbot at all
        if not has_chatbot:
            pain_points.append(PainPoint(
                category="support_automation",
                description="No chatbot or automated support detected",
                severity="high",
                comai_solution="COMAI Chatbot can handle FAQs, order tracking, and product recommendations 24/7",
                confidence=0.95,
                evidence=["No chatbot scripts found in page source"],
            ))

        # WhatsApp only (no proper support)
        if has_whatsapp_widget and not has_live_chat and not has_chatbot:
            pain_points.append(PainPoint(
                category="support_channels",
                description="WhatsApp-only support with no automation",
                severity="high",
                comai_solution="COMAI WhatsApp Bot can automate order tracking, FAQs, and lead qualification",
                confidence=0.90,
                evidence=["WhatsApp widget detected but no live chat or chatbot"],
            ))

        # No live chat
        if not has_live_chat and not has_chatbot:
            pain_points.append(PainPoint(
                category="real_time_support",
                description="No live chat or real-time support capability",
                severity="medium",
                comai_solution="COMAI Live Chat with AI responses for instant customer support",
                confidence=0.85,
                evidence=["No live chat widget detected"],
            ))

        # Large product catalogue without automation
        if product_count > 100 and not has_chatbot:
            pain_points.append(PainPoint(
                category="product_discovery",
                description=f"Large catalogue ({product_count} products) without AI-powered product recommendations",
                severity="medium",
                comai_solution="COMAI Product Recommender can guide customers to the right products",
                confidence=0.80,
                evidence=[f"Detected {product_count} products, no chatbot for guided shopping"],
            ))

        # No CRM detected
        if not has_crm:
            pain_points.append(PainPoint(
                category="customer_management",
                description="No CRM or customer management tool detected",
                severity="medium",
                comai_solution="COMAI CRM Integration can capture and manage customer interactions",
                confidence=0.75,
                evidence=["No HubSpot, Zendesk, or Freshdesk detected"],
            ))

        # Support email only (no phone)
        if email and not phone:
            pain_points.append(PainPoint(
                category="support_accessibility",
                description="Email-only support channel, no phone support",
                severity="low",
                comai_solution="COMAI can add phone-based AI support and callback scheduling",
                confidence=0.70,
                evidence=["Support email found but no phone number"],
            ))

        # Social media presence without automation
        if (instagram_url or facebook_url) and not has_chatbot:
            pain_points.append(PainPoint(
                category="social_commerce",
                description="Active social media without automated customer engagement",
                severity="medium",
                comai_solution="COMAI Social Commerce can automate DM responses and order processing",
                confidence=0.75,
                evidence=["Social media presence detected but no chatbot for engagement"],
            ))

        # Shopify store without chatbot (common pain)
        if platform.lower() == "shopify" and not has_chatbot:
            pain_points.append(PainPoint(
                category="platform_gap",
                description="Shopify store without integrated AI support",
                severity="medium",
                comai_solution="COMAI Shopify Integration provides seamless AI support within the store",
                confidence=0.80,
                evidence=["Shopify detected, no native chatbot integration"],
            ))

        # Calculate total pain score
        severity_weights = {"high": 30, "medium": 20, "low": 10}
        total_score = sum(
            severity_weights.get(p.severity, 10) * p.confidence
            for p in pain_points
        )
        total_score = min(100.0, total_score)

        # Determine top pain and recommended module
        top_pain = ""
        recommended_module = "COMAI Chatbot"
        if pain_points:
            high_pains = [p for p in pain_points if p.severity == "high"]
            if high_pains:
                top_pain = high_pains[0].description
                recommended_module = high_pains[0].comai_solution.split(" can ")[0] if " can " in high_pains[0].comai_solution else "COMAI Chatbot"
            else:
                top_pain = pain_points[0].description
                recommended_module = pain_points[0].comai_solution.split(" can ")[0] if " can " in pain_points[0].comai_solution else "COMAI Chatbot"

        # Generate business value statement
        pain_categories = list(set(p.category for p in pain_points))
        business_value = f"Potential to automate {len(pain_categories)} key areas: {', '.join(pain_categories[:3])}"

        return PainAnalysis(
            pain_points=pain_points,
            total_pain_score=total_score,
            top_pain=top_pain,
            recommended_module=recommended_module,
            business_value=business_value,
        )
