"""Template-only opportunity recommendations."""

from __future__ import annotations

from opportunity_intelligence.models import Opportunity
from opportunity_intelligence.schemas import Recommendation


class RecommendationEngine:
    def build(self, opportunity: Opportunity) -> Recommendation:
        evidence_titles = [item.title for item in opportunity.evidence]
        why_contact = (
            f"{opportunity.company_name} has a verified {opportunity.signal_category} signal: "
            f"{opportunity.signal_title}."
        )
        why_now = (
            f"The signal is {opportunity.signal_age_days} days old and maps to a "
            f"{opportunity.buying_window} buying window."
        )
        return Recommendation(
            why_contact=why_contact,
            why_now=why_now,
            supporting_evidence=evidence_titles,
            buying_window=opportunity.buying_window,
            score_breakdown={
                "intent": opportunity.intent_score,
                "pain": opportunity.pain_score,
                "budget": opportunity.budget_score,
                "growth": opportunity.growth_score,
                "timing": opportunity.timing_score,
                "freshness": opportunity.freshness_score,
                "evidence": opportunity.evidence_score,
                "icp": opportunity.icp_score,
                "final": opportunity.opportunity_score,
            },
        )
