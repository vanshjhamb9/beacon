"""Evidence-based Buyability Scorer.

Every scoring dimension requires EVIDENCE.
No inferences. No guesses. No invented claims.

Scoring model (100 points):
  Business Stage         15
  Growth Signals         20
  Founder Accessibility  15
  Support Pain           15
  WhatsApp               10
  Technology Gap         10
  Marketing Activity      5
  Buying Intent          10

Plus: Buying Intent Score (separate, 0-100)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from packages.ecommerce_leads.models import (
    DetectionState,
    EnrichedEcommerceLead,
)
from packages.qualification_engine.icp_loader import ICPConfig

logger = logging.getLogger(__name__)


@dataclass
class ScoringResult:
    """Result of evidence-based scoring."""

    # Dimension scores (each 0-100)
    business_stage_score: float = 0.0
    growth_signals_score: float = 0.0
    founder_accessibility_score: float = 0.0
    support_pain_score: float = 0.0
    whatsapp_score: float = 0.0
    technology_gap_score: float = 0.0
    marketing_activity_score: float = 0.0
    buying_intent_score: float = 0.0

    # Weighted total (0-100)
    total_score: float = 0.0

    # Buying Intent (separate score, 0-100)
    buying_intent_total: float = 0.0

    # Grade
    grade: str = "NEEDS_ENRICHMENT"

    # Business stage
    business_stage: str = "UNKNOWN"

    # Evidence
    evidence: list[str] = field(default_factory=list)
    evidence_items: list[dict[str, Any]] = field(default_factory=list)
    missing_signals: list[str] = field(default_factory=list)

    # Output
    who_they_are: str = ""
    how_big: str = ""
    are_growing: str = ""
    who_owns: str = ""
    can_reach: str = ""
    what_problem: str = ""
    why_buy_comai: str = ""
    why_now: str = ""
    what_to_say: str = ""


from typing import Any


class BuyabilityScorer:
    """Score leads for BUYABILITY — with evidence."""

    def __init__(self, icp: ICPConfig) -> None:
        self.icp = icp

    def score(self, lead: EnrichedEcommerceLead) -> ScoringResult:
        """Score a lead with evidence-based scoring."""
        result = ScoringResult()

        # Step 1: Check evidence quality
        result.evidence_grade = self._assess_evidence_grade(lead)

        # Step 2: Classify business stage
        result.business_stage = self._classify_business_stage(lead)

        # Step 3: Score each dimension
        result.business_stage_score = self._score_business_stage(lead, result.business_stage)
        result.growth_signals_score = self._score_growth_signals(lead)
        result.founder_accessibility_score = self._score_founder_accessibility(lead)
        result.support_pain_score = self._score_support_pain(lead)
        result.whatsapp_score = self._score_whatsapp(lead)
        result.technology_gap_score = self._score_technology_gap(lead)
        result.marketing_activity_score = self._score_marketing_activity(lead)
        result.buying_intent_score = self._score_buying_intent(lead)

        # Step 4: Calculate weighted total
        weights = self.icp.buyability_scoring
        result.total_score = round(
            result.business_stage_score * weights.get("business_stage", 15) / 100
            + result.growth_signals_score * weights.get("growth_signals", 20) / 100
            + result.founder_accessibility_score * weights.get("founder_accessibility", 15) / 100
            + result.support_pain_score * weights.get("support_pain", 15) / 100
            + result.whatsapp_score * weights.get("whatsapp", 10) / 100
            + result.technology_gap_score * weights.get("technology_gap", 10) / 100
            + result.marketing_activity_score * weights.get("marketing_activity", 5) / 100
            + result.buying_intent_score * weights.get("buying_intent", 10) / 100,
            1,
        )

        # Step 5: Calculate buying intent (separate score)
        result.buying_intent_total = self._calculate_buying_intent(lead)

        # Step 6: Check evidence quality — use evidence grade (A/B/C/D)
        if result.evidence_grade in ("D",):
            result.grade = "NEEDS_ENRICHMENT"
            result.missing_signals = self._identify_missing_signals(lead)
            self._generate_output(lead, result)
            return result

        # Step 7: Assign grade
        result.grade = self._assign_grade(result.total_score, result.buying_intent_total)

        # Step 8: Generate output
        self._generate_output(lead, result)

        return result

    def _assess_evidence_grade(self, lead: EnrichedEcommerceLead) -> str:
        """Assess quality of evidence (A/B/C/D)."""
        score = 0

        if lead.founder_name:
            score += 2
        if lead.email and lead.email_valid:
            score += 2
        if lead.phone:
            score += 1
        if lead.employee_count:
            score += 2
        if lead.product_count and lead.product_count > 1:
            score += 1
        if lead.platform:
            score += 1
        if lead.chatbot_state != DetectionState.UNKNOWN:
            score += 1
        if lead.whatsapp_state != DetectionState.UNKNOWN:
            score += 1
        if lead.social_links:
            score += 1
        if lead.pain_points:
            score += 2
        if lead.growth_signals:
            score += 2
        if lead.buying_signals:
            score += 2

        if score >= 10:
            return "A"
        elif score >= 7:
            return "B"
        elif score >= 4:
            return "C"
        else:
            return "D"

    def _classify_business_stage(self, lead: EnrichedEcommerceLead) -> str:
        """Classify business stage with evidence."""
        emp = lead.employee_count
        products = lead.product_count

        if emp:
            if emp < 10:
                return "EARLY"
            elif emp <= 50:
                return "GROWING"
            elif emp <= 200:
                return "MID_SIZE"
            else:
                return "ENTERPRISE"

        if products and products > 1:
            if products < 30:
                return "EARLY"
            elif products <= 150:
                return "GROWING"
            elif products <= 500:
                return "MID_SIZE"
            else:
                return "ENTERPRISE"

        return "UNKNOWN"

    def _score_business_stage(self, lead: EnrichedEcommerceLead, stage: str) -> float:
        """Score business stage (0-100)."""
        if stage == "GROWING":
            return 100.0
        elif stage == "EARLY":
            return 70.0
        elif stage == "MID_SIZE":
            return 80.0
        elif stage == "ENTERPRISE":
            return 0.0
        else:
            return 30.0  # Unknown — low confidence

    def _score_growth_signals(self, lead: EnrichedEcommerceLead) -> float:
        """Score growth signals with evidence (0-100)."""
        score = 0.0
        signals = lead.growth_signals or []

        for signal in signals:
            signal_type = signal.get("type", "")
            confidence = signal.get("confidence", 0.5)

            if signal_type == "hiring":
                score += 25 * confidence
            elif signal_type == "funding":
                score += 30 * confidence
            elif signal_type == "new_products":
                score += 20 * confidence
            elif signal_type == "expansion":
                score += 20 * confidence
            elif signal_type == "traffic_growth":
                score += 15 * confidence
            elif signal_type == "advertising":
                score += 15 * confidence
            elif signal_type == "social_growth":
                score += 10 * confidence
            elif signal_type == "recent_launch":
                score += 20 * confidence

        # Also count discovery signal from metadata
        metadata = lead.raw.metadata or {}
        if metadata.get("stage") == "growing":
            score += 20
        if metadata.get("signal_text"):
            score += 10

        return min(100.0, score)

    def _score_founder_accessibility(self, lead: EnrichedEcommerceLead) -> float:
        """Score founder accessibility (0-100)."""
        score = 0.0

        if lead.founder_name:
            score += 40
            if lead.founder_confidence >= 0.7:
                score += 10
        if lead.email and lead.email_valid:
            score += 30
        if lead.phone:
            score += 15
        if lead.founder_linkedin:
            score += 10

        return min(100.0, score)

    def _score_support_pain(self, lead: EnrichedEcommerceLead) -> float:
        """Score support pain with evidence (0-100)."""
        score = 0.0

        # No chatbot = high pain (verified absent)
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            score += 35
        elif lead.chatbot_state == DetectionState.VERIFIED_PRESENT:
            score += 5  # Has chatbot but may need upgrade

        # No WhatsApp automation (verified absent)
        if lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            score += 25

        # No CRM (verified absent)
        if lead.crm_state == DetectionState.VERIFIED_ABSENT:
            score += 15

        # Pain point evidence
        pain_points = lead.pain_points or []
        for pain in pain_points:
            confidence = pain.get("confidence", 0.5)
            pain_type = pain.get("type", "")

            if pain_type == "faq_volume":
                score += 10 * confidence
            elif pain_type == "return_policy":
                score += 8 * confidence
            elif pain_type == "shipping_info":
                score += 5 * confidence
            elif pain_type == "large_catalog":
                score += 12 * confidence

        return min(100.0, score)

    def _score_whatsapp(self, lead: EnrichedEcommerceLead) -> float:
        """Score WhatsApp (0-100)."""
        if lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            # No WhatsApp = needs education, lower score
            return 30.0
        elif lead.whatsapp_state == DetectionState.VERIFIED_PRESENT:
            # Has WhatsApp but no automation = opportunity
            return 80.0
        else:
            return 20.0  # Unknown

    def _score_technology_gap(self, lead: EnrichedEcommerceLead) -> float:
        """Score technology gap (0-100)."""
        score = 0.0

        # Shopify or WooCommerce
        if lead.platform in ["shopify", "woocommerce"]:
            score += 50

        # No AI automation at all
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            score += 30
        elif lead.chatbot_state == DetectionState.VERIFIED_PRESENT:
            score += 10

        # No enterprise helpdesk
        if lead.crm_state == DetectionState.VERIFIED_ABSENT:
            score += 20

        return min(100.0, score)

    def _score_marketing_activity(self, lead: EnrichedEcommerceLead) -> float:
        """Score marketing activity (0-100)."""
        score = 0.0

        social_count = len(lead.social_links or {})
        if social_count >= 3:
            score += 40
        elif social_count >= 2:
            score += 30
        elif social_count >= 1:
            score += 15

        if lead.platform:
            score += 30

        if lead.product_count and lead.product_count > 30:
            score += 30

        return min(100.0, score)

    def _score_buying_intent(self, lead: EnrichedEcommerceLead) -> float:
        """Score buying intent (0-100)."""
        score = 0.0

        buying_signals = lead.buying_signals or []
        for signal in buying_signals:
            confidence = signal.get("confidence", 0.5)
            signal_type = signal.get("type", "")

            if signal_type == "hiring":
                score += 20 * confidence
            elif signal_type == "funding":
                score += 25 * confidence
            elif signal_type == "new_store":
                score += 20 * confidence
            elif signal_type == "catalogue_expansion":
                score += 15 * confidence
            elif signal_type == "advertising":
                score += 15 * confidence
            elif signal_type == "technology_migration":
                score += 20 * confidence

        # Pain signals = buying intent
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            score += 15
        if lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            score += 10

        return min(100.0, score)

    def _calculate_buying_intent(self, lead: EnrichedEcommerceLead) -> float:
        """Calculate separate buying intent score (0-100)."""
        score = 0.0

        # Specific buying signals
        buying_signals = lead.buying_signals or []
        for signal in buying_signals:
            signal_type = signal.get("type", "")
            confidence = signal.get("confidence", 0.5)

            if signal_type == "hiring":
                score += 20 * confidence
            elif signal_type == "funding":
                score += 25 * confidence
            elif signal_type == "new_store":
                score += 20 * confidence
            elif signal_type == "catalogue_expansion":
                score += 15 * confidence
            elif signal_type == "advertising":
                score += 15 * confidence
            elif signal_type == "technology_migration":
                score += 20 * confidence

        # PAIN = INTENT (if they're in pain, they're more likely to buy)
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            score += 15
        if lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            score += 10
        if lead.crm_state == DetectionState.VERIFIED_ABSENT:
            score += 5

        # Growth signals = more likely to invest
        growth = lead.growth_signals or []
        for signal in growth:
            if signal.get("type") in ["hiring", "funding"]:
                score += 10 * signal.get("confidence", 0.5)

        return min(100.0, score)

    def _assign_grade(self, total_score: float, buying_intent: float) -> str:
        """Assign qualification grade."""
        # SALES_PROSPECT: high total + some buying intent
        if total_score >= 60 and buying_intent >= 40:
            return "SALES_PROSPECT"
        # HOT_OPPORTUNITY: very high on both
        elif total_score >= 75 and buying_intent >= 60:
            return "HOT_OPPORTUNITY"
        # QUALIFIED: good total but low intent
        elif total_score >= 50:
            return "QUALIFIED"
        # NURTURE: potential but not ready
        elif total_score >= 30:
            return "NURTURE"
        else:
            return "REJECT"

    def _identify_missing_signals(self, lead: EnrichedEcommerceLead) -> list[str]:
        """Identify what signals are missing."""
        missing = []
        if not lead.founder_name:
            missing.append("founder_name")
        if not lead.email or not lead.email_valid:
            missing.append("valid_email")
        if not lead.phone:
            missing.append("phone")
        if not lead.employee_count:
            missing.append("employee_count")
        if not lead.product_count or lead.product_count <= 1:
            missing.append("product_count")
        if not lead.social_links:
            missing.append("social_links")
        if lead.chatbot_state == DetectionState.UNKNOWN:
            missing.append("chatbot_detection")
        if lead.whatsapp_state == DetectionState.UNKNOWN:
            missing.append("whatsapp_detection")
        if not lead.pain_points:
            missing.append("pain_evidence")
        if not lead.growth_signals:
            missing.append("growth_evidence")
        if not lead.buying_signals:
            missing.append("buying_evidence")
        return missing

    def _generate_output(self, lead: EnrichedEcommerceLead, result: ScoringResult) -> None:
        """Generate the 9 output fields with evidence."""
        company = lead.raw.company_name
        industry = lead.raw.industry or "ecommerce"
        city = lead.raw.city or "India"
        products = lead.product_count
        emp = lead.employee_count
        stage = result.business_stage

        # WHO are they?
        result.who_they_are = f"{company} — {industry} brand based in {city}"

        # HOW BIG are they?
        if emp:
            result.how_big = f"{emp} employees"
        elif products and products > 1:
            result.how_big = f"{products} products"
        else:
            result.how_big = "Size unknown — needs enrichment"

        # ARE they growing?
        growth_parts = []
        for signal in (lead.growth_signals or []):
            growth_parts.append(signal.get("evidence", signal.get("type", "")))
        if lead.raw.metadata.get("stage") == "growing":
            growth_parts.append("identified as growing brand")
        result.are_growing = "; ".join(growth_parts[:3]) if growth_parts else "No growth evidence found"

        # WHO owns the company?
        if lead.founder_name:
            result.who_owns = f"{lead.founder_name} ({lead.founder_role or 'role unknown'})"
        else:
            result.who_owns = "Founder not identified"

        # CAN we reach the owner?
        reach_parts = []
        if lead.email and lead.email_valid:
            reach_parts.append(f"email: {lead.email}")
        if lead.phone:
            reach_parts.append(f"phone: {lead.phone}")
        if lead.founder_linkedin:
            reach_parts.append("LinkedIn")
        result.can_reach = "; ".join(reach_parts) if reach_parts else "No contact info"

        # WHAT problem do they likely have?
        problems = []
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            problems.append("no AI chatbot — handling queries manually")
        if lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            problems.append("no WhatsApp automation")
        if lead.crm_state == DetectionState.VERIFIED_ABSENT:
            problems.append("no CRM integration")
        for pain in (lead.pain_points or [])[:2]:
            problems.append(pain.get("evidence", ""))
        result.what_problem = "; ".join(problems[:3]) if problems else "Needs assessment"

        # WHY would they buy COMAI?
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT and lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            result.why_buy_comai = "No AI automation — COMAI can provide 24/7 support + WhatsApp"
        elif lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            result.why_buy_comai = "No chatbot — COMAI can automate customer support"
        elif lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            result.why_buy_comai = "No WhatsApp automation — COMAI can scale engagement"
        else:
            result.why_buy_comai = "Existing automation may need upgrade"

        # WHY NOW?
        why_now_parts = []
        if products and products > 50:
            why_now_parts.append(f"large catalog ({products} products)")
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            why_now_parts.append("manual support is unsustainable")
        for signal in (lead.buying_signals or [])[:1]:
            why_now_parts.append(signal.get("evidence", ""))
        result.why_now = "; ".join(why_now_parts[:2]) if why_now_parts else "Growing business"

        # WHAT should we say?
        founder = lead.founder_name or "there"
        if lead.chatbot_state == DetectionState.VERIFIED_ABSENT and lead.whatsapp_state == DetectionState.VERIFIED_ABSENT:
            result.what_to_say = f"Hi {founder}, noticed {company} is growing. With {products or 'many'} products, customer queries must be overwhelming. We helped similar brands automate 80% of support. Can we show you how?"
        elif lead.chatbot_state == DetectionState.VERIFIED_ABSENT:
            result.what_to_say = f"Hi {founder}, {company} has great WhatsApp presence. But are you handling support manually? We can add AI chatbot to your Shopify store in 48 hours."
        else:
            result.what_to_say = f"Hi {founder}, love what {company} is building. Quick question — how are you handling customer support at scale?"
