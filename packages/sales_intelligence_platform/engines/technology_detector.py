"""Technology Detection Engine - wraps web_scraper tech detection with COMAI scoring.

Determines technology fit score based on detected tech stack and COMAI integration opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TechnologyProfile:
    """Detected technology profile with COMAI fit scoring."""
    platform: str = ""
    ecommerce_platform: str = ""
    support_tools: list[str] = field(default_factory=list)
    analytics_tools: list[str] = field(default_factory=list)
    chatbot_tool: str = ""
    has_whatsapp_widget: bool = False
    has_live_chat: bool = False
    has_crm: bool = False
    crm_tool: str = ""
    comai_fit_score: float = 0.0
    integration_opportunities: list[str] = field(default_factory=list)
    competitive_threats: list[str] = field(default_factory=list)


class TechnologyDetector:
    """Detect technology stack and score COMAI fit."""

    # COMAI integration scores by tool
    TOOL_FIT_SCORES = {
        "shopify": 90,
        "woocommerce": 85,
        "magento": 75,
        "bigcommerce": 80,
        "intercom": 40,  # Competitor
        "zendesk": 35,  # Competitor
        "freshdesk": 45,
        "tidio": 50,
        "gorgias": 40,  # Competitor
        "crisp": 55,
        "livechat": 50,
        "hubspot": 60,
    }

    COMPETITIVE_TOOLS = {"intercom", "zendesk", "gorgias", "drift", "liveperson"}

    def detect(
        self,
        *,
        platform: str = "",
        support_tools: list[str] | None = None,
        analytics_tools: list[str] | None = None,
        chatbot_tool: str = "",
        has_whatsapp_widget: bool = False,
        has_live_chat: bool = False,
        has_crm: bool = False,
        crm_tool: str = "",
    ) -> TechnologyProfile:
        """Analyze technology stack and compute COMAI fit."""
        support_tools = support_tools or []
        analytics_tools = analytics_tools or []

        profile = TechnologyProfile(
            platform=platform,
            ecommerce_platform=platform,
            support_tools=support_tools,
            analytics_tools=analytics_tools,
            chatbot_tool=chatbot_tool,
            has_whatsapp_widget=has_whatsapp_widget,
            has_live_chat=has_live_chat,
            has_crm=has_crm,
            crm_tool=crm_tool,
        )

        # Calculate COMAI fit score
        score = 50.0  # Base score

        # Platform bonus
        platform_scores = {"shopify": 20, "woocommerce": 15, "magento": 10, "bigcommerce": 12}
        score += platform_scores.get(platform.lower(), 0)

        # No chatbot = high opportunity
        if not chatbot_tool:
            score += 25
            profile.integration_opportunities.append("No existing chatbot - greenfield opportunity")
        elif chatbot_tool.lower() in self.COMPETITIVE_TOOLS:
            score += 15
            profile.competitive_threats.append(f"Using competitor: {chatbot_tool}")
            profile.integration_opportunities.append(f"Can replace {chatbot_tool} with COMAI")

        # WhatsApp widget = integration path
        if has_whatsapp_widget:
            score += 10
            profile.integration_opportunities.append("WhatsApp widget detected - can integrate COMAI WhatsApp Bot")

        # No live chat
        if not has_live_chat:
            score += 5
            profile.integration_opportunities.append("No live chat - can add COMAI Live Chat")

        # CRM integration opportunity
        if has_crm and crm_tool:
            score += 5
            profile.integration_opportunities.append(f"CRM ({crm_tool}) detected - can integrate for lead capture")

        # Cap score at 100
        profile.comai_fit_score = min(100.0, score)

        return profile
