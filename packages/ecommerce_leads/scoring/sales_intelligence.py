"""Sales intelligence generator for ecommerce leads."""

from __future__ import annotations

import logging
from packages.ecommerce_leads.models import EnrichedEcommerceLead

logger = logging.getLogger(__name__)


class SalesIntelligenceGenerator:
    """Generate sales intelligence for each lead.
    
    Every exported lead must include:
    - Why contact?
    - Likely pain?
    - Recommended COMAI feature?
    - 30-second opener
    - Confidence
    """

    def generate(self, lead: EnrichedEcommerceLead) -> EnrichedEcommerceLead:
        """Generate sales intelligence for a lead."""
        lead.call_opener = self._generate_call_opener(lead)
        lead.pitch_angle = self._generate_pitch_angle(lead)
        lead.recommended_feature = self._generate_recommended_feature(lead)
        lead.opportunity_summary = self._generate_opportunity_summary(lead)
        return lead

    def _generate_call_opener(self, lead: EnrichedEcommerceLead) -> str:
        """Generate a 30-second call opener."""
        company = lead.raw.company_name
        industry = lead.raw.industry or "ecommerce"
        platform = lead.raw.platform if lead.raw.platform != "unknown" else "online store"

        # Build opener based on available data
        opener_parts = []

        # Greeting with name if available
        if lead.founder_name:
            opener_parts.append(f"Hi {lead.founder_name},")
        else:
            opener_parts.append("Hi,")

        opener_parts.append(f"I noticed {company} has a great {platform} store in the {industry} space.")

        # Add pain point if available
        if lead.pain_points:
            pain = lead.pain_points[0]
            opener_parts.append(f"I was wondering about your customer support setup - {pain.lower()}.")

        # Add value proposition
        opener_parts.append(
            "We help brands like yours automate customer conversations with AI, "
            "handling queries, order tracking, and product recommendations 24/7."
        )

        # Add social proof or specific feature
        if lead.chatbot_detected:
            opener_parts.append("I see you already have a chatbot - we could help you upgrade to a smarter solution.")
        elif lead.whatsapp_detected:
            opener_parts.append("I noticed you use WhatsApp - we can help automate those conversations at scale.")

        opener_parts.append("Would you be open to a quick 10-minute demo?")

        return " ".join(opener_parts)

    def _generate_pitch_angle(self, lead: EnrichedEcommerceLead) -> str:
        """Generate a pitch angle based on lead profile."""
        angles = []

        if lead.shopify_detected:
            angles.append("Shopify-native AI integration")
        elif lead.woocommerce_detected:
            angles.append("WooCommerce AI customer support")
        elif lead.magento_detected:
            angles.append("Magento AI automation")

        if lead.chatbot_detected:
            angles.append("Chatbot upgrade to AI-powered assistant")
        else:
            angles.append("First AI chatbot deployment")

        if lead.whatsapp_detected:
            angles.append("WhatsApp automation with AI")

        if lead.raw.product_count and lead.raw.product_count > 100:
            angles.append("Large catalog support automation")

        if not angles:
            angles.append("AI customer support for ecommerce")

        return " | ".join(angles[:3])

    def _generate_recommended_feature(self, lead: EnrichedEcommerceLead) -> str:
        """Recommend the most relevant COMAI feature."""
        if lead.chatbot_detected:
            return "AI Chatbot Upgrade - Replace existing chatbot with smarter AI"
        if lead.whatsapp_detected:
            return "WhatsApp AI Automation - Automate WhatsApp conversations"
        if lead.raw.product_count and lead.raw.product_count > 100:
            return "Product Recommendation AI - Smart suggestions for large catalogs"
        return "AI Customer Support - 24/7 automated customer service"

    def _generate_opportunity_summary(self, lead: EnrichedEcommerceLead) -> str:
        """Generate a brief opportunity summary."""
        parts = []

        parts.append(f"{lead.raw.company_name} is an Indian {lead.raw.industry or 'ecommerce'} business")

        if lead.raw.platform and lead.raw.platform != "unknown":
            parts.append(f"running on {lead.raw.platform}")
        else:
            parts.append("with an online presence")

        if lead.raw.product_count:
            parts.append(f"offering {lead.raw.product_count}+ products")

        # Key opportunity
        opportunities = []
        if not lead.chatbot_detected:
            opportunities.append("no AI customer support")
        if not lead.whatsapp_detected:
            opportunities.append("no WhatsApp automation")
        if lead.raw.product_count and lead.raw.product_count > 100:
            opportunities.append("large catalog needing automation")

        if opportunities:
            parts.append(f"Key opportunity: {', '.join(opportunities[:2])}")

        return ". ".join(parts) + "."
