"""Deterministic COMAI lead scoring for ecommerce businesses."""

from __future__ import annotations

from packages.ecommerce_leads.models import EnrichedEcommerceLead


class EcommerceScorer:
    """Calculate COMAI opportunity score for ecommerce leads.

    Deterministic scoring - no GPT dependency.

    Scoring breakdown (max 100):
        Technology Fit:         +25  (Shopify/WooCommerce store)
        Business Size:         +20  (more products/pages/social activity)
        Customer Support Opp:  +20  (no chatbot detected)
        WhatsApp Usage:        +15  (WhatsApp presence)
        D2C Brand:             +10  (D2C brand indicators)
        Active Social:         +10  (social media presence)
    """

    def score(self, lead: EnrichedEcommerceLead) -> EnrichedEcommerceLead:
        """Calculate the COMAI score and classify the lead."""
        total = 0.0
        reasons: list[str] = []
        pain_points: list[str] = []

        total += self._score_technology_fit(lead, reasons, pain_points)
        total += self._score_business_size(lead, reasons, pain_points)
        total += self._score_customer_support_opportunity(lead, reasons, pain_points)
        total += self._score_whatsapp(lead, reasons, pain_points)
        total += self._score_d2c_brand(lead, reasons, pain_points)
        total += self._score_social_presence(lead, reasons, pain_points)

        total = min(100.0, total)

        lead.comai_score = total
        lead.lead_priority = self._classify(total)
        lead.sales_reason = "; ".join(reasons) if reasons else self._generate_default_reason(lead)
        lead.pain_points = pain_points if pain_points else self._generate_default_pain_points(lead)

        return lead

    def _score_technology_fit(
        self,
        lead: EnrichedEcommerceLead,
        reasons: list[str],
        pain_points: list[str],
    ) -> float:
        """+25 for Shopify/WooCommerce store."""
        if lead.shopify_detected:
            reasons.append("Shopify store detected - high COMAI fit")
            return 25.0
        if lead.woocommerce_detected:
            reasons.append("WooCommerce store detected - high COMAI fit")
            return 25.0
        if lead.magento_detected:
            reasons.append("Magento store detected - moderate COMAI fit")
            return 20.0
        if lead.raw.platform and lead.raw.platform != "unknown":
            reasons.append(f"Ecommerce platform detected: {lead.raw.platform}")
            return 15.0
        # Partial credit for Indian ecommerce without platform detection
        if lead.raw.country == "India" and lead.raw.product_count > 0:
            reasons.append("Indian ecommerce business (platform pending verification)")
            return 10.0
        return 0.0

    def _score_business_size(
        self,
        lead: EnrichedEcommerceLead,
        reasons: list[str],
        pain_points: list[str],
    ) -> float:
        """+20 for business size indicators."""
        score = 0.0

        if lead.raw.product_count >= 100:
            score += 15.0
            reasons.append(f"Large product catalog ({lead.raw.product_count}+ products)")
        elif lead.raw.product_count >= 30:
            score += 10.0
            reasons.append(f"Medium product catalog ({lead.raw.product_count} products)")
        elif lead.raw.product_count > 0:
            score += 5.0
            reasons.append(f"Product catalog ({lead.raw.product_count} products)")

        if len(lead.raw.social_links) >= 3:
            score += 5.0
            reasons.append("Strong social presence across platforms")
        elif len(lead.raw.social_links) >= 1:
            score += 3.0

        if lead.raw.description and len(lead.raw.description) > 100:
            score += 2.0

        return min(20.0, score)

    def _score_customer_support_opportunity(
        self,
        lead: EnrichedEcommerceLead,
        reasons: list[str],
        pain_points: list[str],
    ) -> float:
        """+20 when no chatbot detected (COMAI opportunity)."""
        if not lead.chatbot_detected:
            reasons.append("No chatbot detected - strong COMAI opportunity")
            pain_points.append("No automated customer support")
            pain_points.append("Customer queries likely handled manually")
            return 20.0
        else:
            reasons.append("Chatbot detected - may need upgrade to COMAI")
            pain_points.append("Existing chatbot may need improvement")
            return 8.0

    def _score_whatsapp(
        self,
        lead: EnrichedEcommerceLead,
        reasons: list[str],
        pain_points: list[str],
    ) -> float:
        """+15 for WhatsApp usage."""
        if lead.whatsapp_detected:
            reasons.append("WhatsApp detected on website - automation opportunity")
            pain_points.append("WhatsApp could be automated with COMAI")
            return 15.0
        return 5.0

    def _score_d2c_brand(
        self,
        lead: EnrichedEcommerceLead,
        reasons: list[str],
        pain_points: list[str],
    ) -> float:
        """+10 for D2C brand indicators."""
        d2c_indicators = [
            "d2c", "direct to consumer", "direct-to-consumer",
            "own brand", "our brand", "private label",
        ]
        text = f"{lead.raw.description} {lead.raw.category} {lead.raw.company_name}".lower()

        if any(indicator in text for indicator in d2c_indicators):
            reasons.append("D2C brand detected")
            return 10.0

        if lead.raw.category in [
            "beauty", "skincare", "cosmetics", "fashion",
            "supplements", "grooming", "wellness",
        ]:
            reasons.append(f"D2C-style category: {lead.raw.category}")
            return 8.0

        return 0.0

    def _score_social_presence(
        self,
        lead: EnrichedEcommerceLead,
        reasons: list[str],
        pain_points: list[str],
    ) -> float:
        """+10 for active social presence."""
        platforms = set(lead.raw.social_links.keys())
        if len(platforms) >= 3:
            reasons.append(f"Active on {len(platforms)} social platforms")
            return 10.0
        elif len(platforms) >= 2:
            reasons.append(f"Active on {len(platforms)} social platforms")
            return 7.0
        elif len(platforms) >= 1:
            reasons.append(f"Active on {list(platforms)[0]}")
            return 4.0
        return 0.0

    def _classify(self, score: float) -> str:
        """Classify lead priority based on score."""
        if score >= 90:
            return "HOT"
        elif score >= 70:
            return "WARM"
        else:
            return "LOW"

    def _generate_default_reason(self, lead: EnrichedEcommerceLead) -> str:
        """Generate a default sales reason when none detected."""
        parts = []
        if lead.raw.country == "India":
            parts.append("Indian ecommerce business")
        if lead.raw.product_count > 0:
            parts.append(f"with {lead.raw.product_count}+ products")
        if lead.raw.industry:
            parts.append(f"in {lead.raw.industry} vertical")
        return "; ".join(parts) if parts else "Ecommerce business with growth potential"

    def _generate_default_pain_points(self, lead: EnrichedEcommerceLead) -> list[str]:
        """Generate default pain points based on available data."""
        pain_points = []
        
        if not lead.chatbot_detected:
            pain_points.append("No automated customer support")
        if not lead.whatsapp_detected:
            pain_points.append("No WhatsApp integration")
        if not lead.crm_detected:
            pain_points.append("No CRM integration detected")
        if len(lead.raw.social_links) == 0:
            pain_points.append("Limited social media presence")
        if lead.raw.product_count > 100:
            pain_points.append("Large catalog may need automated support")
        if lead.raw.country == "India":
            pain_points.append("Indian market - high customer support demand")
            
        return pain_points if pain_points else ["Ecommerce business with growth potential"]
