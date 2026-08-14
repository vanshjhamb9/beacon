"""Sales intelligence generator for COMAI leads.

Takes a BuyabilityResult and generates actionable sales intelligence:
- Summary
- Challenges
- Pitch
- Objections & responses
- Meeting strategy
- Close probability
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.ecommerce_leads.models import EnrichedEcommerceLead
from packages.qualification_engine.scorer import BuyabilityResult


@dataclass
class SalesIntelligence:
    """Actionable sales intelligence for a lead."""

    summary: str = ""
    challenges: list[str] | None = None
    pitch: str = ""
    objection_responses: dict[str, str] | None = None
    meeting_strategy: str = ""
    close_probability: float = 0.0
    recommended_service: str = ""
    priority_action: str = ""

    def __post_init__(self) -> None:
        if self.challenges is None:
            self.challenges = []
        if self.objection_responses is None:
            self.objection_responses = {}


def generate_sales_intelligence(
    lead: EnrichedEcommerceLead,
    result: BuyabilityResult,
) -> SalesIntelligence:
    """Generate sales intelligence from buyability result."""
    intel = SalesIntelligence()

    company = lead.raw.company_name
    stage = result.business_stage

    # Summary
    intel.summary = (
        f"{company} is a {stage}-stage {lead.raw.industry or 'ecommerce'} brand "
        f"based in {lead.raw.city or 'India'}. "
        f"Buyability score: {result.total_score}/100 ({result.grade}). "
    )
    if result.evidence:
        intel.summary += f"Key signals: {', '.join(result.evidence[:3])}."

    # Challenges
    challenges = []
    if not lead.chatbot_detected:
        challenges.append("No AI chatbot — handling customer queries manually")
    if not lead.whatsapp_detected:
        challenges.append("No WhatsApp automation — missing a key channel")
    if not lead.crm_detected:
        challenges.append("No CRM — customer data scattered")
    if lead.raw.product_count and lead.raw.product_count > 50:
        challenges.append(f"Large catalog ({lead.raw.product_count} products) generating high support volume")
    intel.challenges = challenges

    # Pitch
    if not lead.chatbot_detected and not lead.whatsapp_detected:
        intel.pitch = (
            f"We help {company} automate customer support with AI. "
            f"With {lead.raw.product_count or 'many'} products, your team must be drowning in queries. "
            f"Our AI chatbot handles 80% of questions instantly — 24/7."
        )
    elif not lead.chatbot_detected:
        intel.pitch = (
            f"You're doing great on WhatsApp. But what about the rest? "
            f"An AI chatbot on your Shopify store can handle queries while your team focuses on growth."
        )
    else:
        intel.pitch = (
            f"Love what {company} is building. Quick question — "
            f"how are you handling customer support at scale?"
        )

    # Objection responses
    intel.objection_responses = {
        "too_expensive": (
            "COMAI starts at ₹500/month — less than one part-time support agent. "
            "And it works 24/7. Most brands see ROI in the first week."
        ),
        "already_have_shopify_apps": (
            "Shopify apps handle basic FAQs. COMAI handles complex questions, "
            "order tracking, returns — the stuff that eats your team's time."
        ),
        "need_to_see_roi": (
            "Happy to show you a demo with real customer queries. "
            "We can also do a 2-week pilot — if it doesn't save you time, you don't pay."
        ),
        "current_setup_works": (
            "That's great. But are you measuring response time? Customer satisfaction? "
            "Most brands we talk to are surprised by how many queries go unanswered."
        ),
        "too_small": (
            "Actually, 10-50 employee brands are our sweet spot. "
            "You're big enough to have support volume, but small enough that every missed query hurts."
        ),
    }

    # Meeting strategy
    intel.meeting_strategy = (
        f"1. Lead with their pain: 'How are you handling {lead.raw.industry or 'customer'} queries at scale?'\n"
        f"2. Show demo of AI handling a real query similar to their products.\n"
        f"3. Emphasize: 24/7 availability, 80% automation, ₹500/month.\n"
        f"4. Offer 2-week pilot with no commitment."
    )

    # Close probability
    score = result.total_score
    if score >= 85:
        intel.close_probability = 0.7
    elif score >= 70:
        intel.close_probability = 0.5
    elif score >= 55:
        intel.close_probability = 0.3
    else:
        intel.close_probability = 0.15

    # Recommended service
    if not lead.chatbot_detected and not lead.whatsapp_detected:
        intel.recommended_service = "AI Chatbot + WhatsApp Automation (Full Suite)"
    elif not lead.chatbot_detected:
        intel.recommended_service = "AI Chatbot for Commerce"
    elif not lead.whatsapp_detected:
        intel.recommended_service = "WhatsApp AI Automation"
    else:
        intel.recommended_service = "CRM Integration + Workflow Automation"

    # Priority action
    if result.grade == "SALES_READY":
        intel.priority_action = "Reach out within 24 hours. Founder likely accessible."
    elif result.grade == "QUALIFIED":
        intel.priority_action = "Add to nurture sequence. Follow up Day 1, 3, 6."
    elif result.grade == "NURTURE":
        intel.priority_action = "Long-term nurture. Check back in 30 days."
    else:
        intel.priority_action = "Needs enrichment before outreach."

    return intel
