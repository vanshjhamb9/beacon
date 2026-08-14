"""Call Preparation Generator - deterministic, no LLM.

Generates call scripts, objection handling, and demo preparation
for sales calls with leads.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CallPreparation:
    """Complete call preparation kit for a sales call."""
    thirty_second_opener: str = ""
    likely_objections: list[dict[str, str]] = field(default_factory=list)
    suggested_responses: list[dict[str, str]] = field(default_factory=list)
    demo_angle: str = ""
    recommended_features: list[str] = field(default_factory=list)
    meeting_objective: str = ""
    follow_up_actions: list[str] = field(default_factory=list)


class CallPreparationGenerator:
    """Generate call preparation materials for sales calls."""

    def generate(
        self,
        *,
        company_name: str = "",
        category: str = "",
        platform: str = "",
        pain_points: list[dict] | None = None,
        has_chatbot: bool = False,
        chatbot_tool: str = "",
        product_count: int = 0,
        decision_maker_name: str = "",
        decision_maker_role: str = "",
        city: str = "",
        instagram_followers: int = 0,
        whatsapp_link: str = "",
        has_ecommerce: bool = True,
    ) -> CallPreparation:
        """Generate complete call preparation kit."""
        pain_points = pain_points or []
        prep = CallPreparation()

        pain_categories = [p.get("category", "") for p in pain_points]
        top_pain = pain_points[0] if pain_points else {}
        pain_desc = top_pain.get("description", "customer support challenges")

        # 30-second opener
        if decision_maker_name:
            opener_name = decision_maker_name.split()[0] if decision_maker_name else ""
            prep.thirty_second_opener = (
                f"Hi {opener_name}, I'm from COMAI. We help {category or 'ecommerce'} brands like {company_name} "
                f"automate customer support and boost sales with AI. I noticed you don't have a chatbot on your site — "
                f"we typically save teams like yours 20+ hours a week on repetitive queries. Can I show you how?"
            )
        else:
            prep.thirty_second_opener = (
                f"Hi, I'm from COMAI. We help {category or 'ecommerce'} brands like {company_name} "
                f"automate customer support and boost sales with AI. I noticed you don't have a chatbot on your site — "
                f"we typically save teams like yours 20+ hours a week on repetitive queries. Can I show you how?"
            )

        # Likely objections and responses
        prep.likely_objections = [
            {
                "objection": "We already have support staff handling queries",
                "response": "That's great! COMAI doesn't replace your team — it handles the 80% of repetitive questions (order status, FAQs, product info) so your team can focus on complex issues that need a human touch.",
            },
            {
                "objection": "We're too small to need AI",
                "response": "Actually, smaller teams benefit the most. With {product_count} products, you're likely getting dozens of daily queries about order tracking and product recommendations. COMAI handles those 24/7 while you focus on growth.".format(product_count=product_count or "many"),
            },
            {
                "objection": "How much does it cost?",
                "response": "We have plans starting from ₹999/month. Most clients see ROI within the first week from reduced support workload and increased conversions. We also offer a free trial so you can see the impact firsthand.",
            },
            {
                "objection": "Will it work with our Shopify store?",
                "response": "Yes! COMAI integrates seamlessly with Shopify, WooCommerce, and other platforms. Setup takes less than 10 minutes with no coding required.",
            },
            {
                "objection": "We use WhatsApp for support already",
                "response": "Perfect! Our WhatsApp Bot can automate responses to common queries, track orders, and even send personalized product recommendations — all while your team handles complex cases.",
            },
        ]

        # Demo angle
        if not has_chatbot:
            prep.demo_angle = (
                f"Show how COMAI can handle {company_name}'s most common customer queries: "
                f"order tracking, product recommendations, and FAQ responses. "
                f"Use real examples from their website to demonstrate the AI's understanding."
            )
        elif chatbot_tool:
            prep.demo_angle = (
                f"Show how COMAI can enhance or replace their current {chatbot_tool} with better AI capabilities, "
                f"lower costs, and more features like WhatsApp integration and product recommendations."
            )
        else:
            prep.demo_angle = (
                f"Show how COMAI's AI-powered platform can handle {company_name}'s customer support "
                f"with natural language understanding and seamless handoff to human agents."
            )

        # Recommended features to showcase
        if "support_automation" in pain_categories or not has_chatbot:
            prep.recommended_features.append("AI Chatbot for 24/7 customer support")
        if "product_discovery" in pain_categories or product_count > 100:
            prep.recommended_features.append("AI Product Recommender")
        if "social_commerce" in pain_categories or instagram_followers > 10000:
            prep.recommended_features.append("Social Commerce Automation")
        if whatsapp_link or "support_channels" in pain_categories:
            prep.recommended_features.append("WhatsApp Bot Integration")
        if not prep.recommended_features:
            prep.recommended_features = [
                "AI Chatbot for customer support",
                "Order tracking automation",
                "Product recommendations",
            ]

        # Meeting objective
        prep.meeting_objective = (
            f"1. Understand {company_name}'s current customer support challenges\n"
            f"2. Show how COMAI can automate their top 3 support queries\n"
            f"3. Present a tailored demo using their actual products\n"
            f"4. Propose a free trial to measure impact"
        )

        # Follow-up actions
        prep.follow_up_actions = [
            "Send personalized demo link with their products pre-loaded",
            "Share case study of similar brand in their category",
            "Schedule technical setup call if trial approved",
            "Add to email nurture sequence with industry-specific content",
        ]

        return prep
