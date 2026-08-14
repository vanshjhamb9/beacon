"""Sales Intelligence Summary Generator - deterministic, no LLM.

Generates the "Why COMAI" narrative, recommended pitch, and competitive positioning
for each lead based on detected pain points and technology stack.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SalesIntelligenceSummary:
    """Complete sales intelligence summary for a lead."""
    why_comai: str = ""
    biggest_pain_point: str = ""
    recommended_pitch: str = ""
    expected_business_value: str = ""
    pitch_angle: str = ""
    competitive_position: str = ""
    urgency: str = ""  # high, medium, low
    target_person: str = ""


class SalesIntelligenceGenerator:
    """Generate sales intelligence summaries from pain points and tech data."""

    def generate(
        self,
        *,
        company_name: str = "",
        category: str = "",
        platform: str = "",
        pain_points: list[dict] | None = None,
        has_chatbot: bool = False,
        chatbot_tool: str = "",
        has_whatsapp: bool = False,
        has_live_chat: bool = False,
        product_count: int = 0,
        city: str = "",
        decision_maker_name: str = "",
        decision_maker_role: str = "",
    ) -> SalesIntelligenceSummary:
        """Generate complete sales intelligence summary."""
        pain_points = pain_points or []
        summary = SalesIntelligenceSummary()

        # Determine target person
        if decision_maker_name:
            summary.target_person = decision_maker_name
        elif decision_maker_role:
            summary.target_person = f"The {decision_maker_role}"
        else:
            summary.target_person = "The founder or operations head"

        # Build "Why COMAI" narrative
        pain_descriptions = [p.get("description", "") for p in pain_points if p.get("severity") == "high"]
        if not pain_descriptions:
            pain_descriptions = [p.get("description", "") for p in pain_points[:3]]

        if pain_descriptions:
            summary.why_comai = (
                f"{company_name} currently faces: {'; '.join(pain_descriptions[:3])}. "
                f"COMAI can automate these processes, reducing manual work and improving customer experience."
            )
        else:
            summary.why_comai = (
                f"{company_name} is a growing {category or 'ecommerce'} brand on {platform or 'their platform'}. "
                f"COMAI can help them scale customer support and sales operations with AI automation."
            )

        # Determine biggest pain point
        if not has_chatbot:
            summary.biggest_pain_point = "No automated customer support - likely handling all queries manually"
        elif has_whatsapp and not has_live_chat:
            summary.biggest_pain_point = "WhatsApp-only support without AI automation"
        elif product_count > 100:
            summary.biggest_pain_point = f"Large product catalogue ({product_count} items) without AI-powered product discovery"
        else:
            summary.biggest_pain_point = "Opportunity to enhance customer experience with AI"

        # Generate pitch angle
        if not has_chatbot and product_count > 50:
            summary.pitch_angle = (
                f"With {product_count}+ products and no chatbot, {company_name} is likely spending significant "
                f"resources on repetitive customer queries about order tracking, product recommendations, and FAQs. "
                f"COMAI can automate 80% of these interactions."
            )
        elif not has_chatbot:
            summary.pitch_angle = (
                f"{company_name} has no automated support. COMAI can immediately reduce their support workload "
                f"by handling FAQs, order status, and product questions with AI."
            )
        elif has_whatsapp and not has_live_chat:
            summary.pitch_angle = (
                f"{company_name} uses WhatsApp for support but without automation. "
                f"COMAI WhatsApp Bot can handle customer queries 24/7 while their team focuses on growth."
            )
        else:
            summary.pitch_angle = (
                f"COMAI can enhance {company_name}'s customer experience with AI-powered support, "
                f"reducing response times and increasing conversion rates."
            )

        # Recommended pitch
        pain_categories = list(set(p.get("category", "") for p in pain_points))
        if "support_automation" in pain_categories or "real_time_support" in pain_categories:
            summary.recommended_pitch = (
                "Start with COMAI Chatbot to automate customer support. "
                "Expect 60-80% reduction in support tickets within 30 days."
            )
        elif "product_discovery" in pain_categories:
            summary.recommended_pitch = (
                "COMAI Product Recommender can guide customers to the right products, "
                "increasing average order value by 15-25%."
            )
        elif "social_commerce" in pain_categories:
            summary.recommended_pitch = (
                "COMAI Social Commerce can automate DM responses and convert social followers into customers."
            )
        else:
            summary.recommended_pitch = (
                "COMAI provides a complete AI-powered customer support and sales automation platform. "
                "Start with a free trial to see immediate impact."
            )

        # Expected business value
        if product_count > 200:
            summary.expected_business_value = (
                f"With {product_count}+ products, automating support could save 20-40 hours/week "
                f"and increase conversion rates by 15-30%."
            )
        elif product_count > 50:
            summary.expected_business_value = (
                f"Automating repetitive queries could save 10-20 hours/week "
                f"and improve customer satisfaction scores."
            )
        else:
            summary.expected_business_value = (
                "AI automation can free up the team to focus on growth "
                "while providing 24/7 customer support."
            )

        # Competitive position
        if not has_chatbot:
            summary.competitive_position = (
                "Many competitors in this space already use chatbots. "
                "COMAI can help them catch up and gain a competitive advantage."
            )
        else:
            summary.competitive_position = (
                "COMAI can enhance their existing support stack with AI capabilities."
            )

        # Urgency
        high_pains = [p for p in pain_points if p.get("severity") == "high"]
        if len(high_pains) >= 2:
            summary.urgency = "high"
        elif len(high_pains) >= 1:
            summary.urgency = "medium"
        else:
            summary.urgency = "low"

        return summary
