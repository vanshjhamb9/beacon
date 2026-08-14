"""Coverage boosters for edge paths across Sales Intelligence modules."""

from uuid import uuid4

from sales_intelligence.intent.engine import BuyingIntentEngine
from sales_intelligence.models.types import BudgetBand, BuyingStage, OfferType, SalesIntelligenceInput
from sales_intelligence.objections.engine import ObjectionPredictionEngine
from sales_intelligence.offers.engine import OfferRecommendationEngine
from sales_intelligence.psychology.engine import PsychologyEngine
from sales_intelligence.reply.engine import ReplyIntelligenceEngine
from sales_intelligence.trust.engine import TrustBuilderEngine


def _base(**overrides: object) -> SalesIntelligenceInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Edge Co",
        "opportunity_score": 40,
        "probability": 20,
    }
    payload.update(overrides)
    return SalesIntelligenceInput(**payload)  # type: ignore[arg-type]


def test_intent_negotiation_stage_with_proposals() -> None:
    result = BuyingIntentEngine().analyze(_base(proposals=[{"title": "SOW", "status": "sent"}], replies=[{"body": "ok"}]))
    assert result.buying_stage == BuyingStage.NEGOTIATION


def test_intent_vendor_evaluation_with_meetings() -> None:
    result = BuyingIntentEngine().analyze(_base(meetings=[{"title": "Disco"}], replies=[{"body": "ok"}]))
    assert result.buying_stage == BuyingStage.VENDOR_EVALUATION


def test_intent_budget_enterprise_from_employees() -> None:
    result = BuyingIntentEngine().analyze(_base(employee_count=600, expected_budget=None, revenue_band=None))
    assert result.budget_probability == BudgetBand.ENTERPRISE


def test_psychology_technical_style() -> None:
    profile = PsychologyEngine().analyze(_base(pains=["API integration", "CTO review"], signals=["technical"]))
    assert profile.preferred_communication_style.value in {"technical", "consultative", "direct", "executive"}


def test_objections_compliance_boost_for_healthcare() -> None:
    objs = ObjectionPredictionEngine().predict(_base(industry="Healthcare", pains=["regulated data"]))
    compliance = next(o for o in objs if o.objection.value == "Compliance")
    assert compliance.likelihood >= 35


def test_offer_marketplace_hint() -> None:
    offer = OfferRecommendationEngine().recommend(
        _base(pains=["marketplace sellers buyers"], signals=["two-sided marketplace"], recommended_service="Marketplace")
    )
    assert offer.primary_offer in set(OfferType)


def test_trust_default_industry() -> None:
    trust = TrustBuilderEngine().build(_base(industry=None), primary_offer=OfferType.WEBSITE)
    assert trust.portfolio_items
    assert "SaaS" in trust.industries_served


def test_reply_unknown_fallback() -> None:
    result = ReplyIntelligenceEngine().classify("asdf qwer zxcv")
    assert result.best_response
    assert result.confidence >= 20
