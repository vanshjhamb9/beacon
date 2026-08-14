from __future__ import annotations

from sales_intelligence.models.types import (
    BuyingIntentResult,
    OfferRecommendation,
    PredictedObjection,
    PsychologyProfile,
    SalesIntelligenceInput,
    SalesScore,
)


class SalesScoreEngine:
    def score(
        self,
        item: SalesIntelligenceInput,
        *,
        intent: BuyingIntentResult,
        psychology: PsychologyProfile,
        objections: list[PredictedObjection],
        offer: OfferRecommendation,
    ) -> SalesScore:
        deal = min(95.0, intent.buying_intent_score * 0.55 + item.probability * 0.25 + (10.0 if item.replies else 0.0) + (8.0 if item.meetings else 0.0))
        revenue = min(95.0, deal * 0.7 + (15.0 if intent.budget_probability.value in {"high", "enterprise"} else 5.0) + min(10.0, item.opportunity_score * 0.1))
        size = offer.expected_value or item.expected_budget or "$25k–$45k"
        health = min(100.0, 40.0 + (15.0 if item.replies else 0.0) + (15.0 if item.meetings else 0.0) + (10.0 if item.proposals else 0.0) + intent.buying_confidence * 0.2)
        rel = min(100.0, 30.0 + len(item.emails) * 4.0 + len(item.replies) * 8.0 + len(item.meetings) * 10.0 + len(item.notes) * 2.0)
        top_obj = objections[0].likelihood if objections else 30.0
        competition = min(90.0, 25.0 + (20.0 if item.vendors else 0.0) + top_obj * 0.35)
        close = min(95.0, deal * 0.6 + (15.0 if item.proposals else 0.0) + (10.0 if psychology.pain_intensity >= 60 else 0.0) - competition * 0.15)
        evidence = [
            f"intent:{intent.buying_intent_score}",
            f"probability:{item.probability}",
            f"replies:{len(item.replies)}",
            f"meetings:{len(item.meetings)}",
            f"competition:{round(competition, 2)}",
            f"primary_offer:{offer.primary_offer.value}",
        ]
        return SalesScore(
            deal_probability=round(deal, 4),
            revenue_probability=round(revenue, 4),
            expected_deal_size=str(size),
            sales_health=round(health, 4),
            relationship_health=round(rel, 4),
            competition_risk=round(competition, 4),
            close_probability=round(max(0.0, close), 4),
            evidence=evidence,
        )
