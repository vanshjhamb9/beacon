from uuid import uuid4

from sales_intelligence import SCORING_VERSION, SalesIntelligencePipeline, SalesIntelligenceService
from sales_intelligence.models.types import SalesIntelligenceInput


def _item(**overrides: object) -> SalesIntelligenceInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Beacon Buyer Co",
        "industry": "SaaS",
        "employee_count": 80,
        "funding_days_ago": 40,
        "technologies": ["Next.js", "Postgres"],
        "pains": ["manual workflows", "scaling issues"],
        "signals": ["hiring", "funding"],
        "hiring_count": 4,
        "decision_makers": [{"name": "Jordan Lee", "title": "CTO"}],
        "recommended_service": "Custom SaaS",
        "opportunity_score": 78,
        "priority_grade": "A",
        "probability": 65,
        "replies": [{"body": "Interested — send a proposal", "subject": "Re"}],
        "emails": [{"subject": "Hello", "body": "Intro"}],
        "vendors": [],
    }
    payload.update(overrides)
    return SalesIntelligenceInput(**payload)  # type: ignore[arg-type]


def test_pipeline_produces_full_decision_pack() -> None:
    decision = SalesIntelligencePipeline().process(_item())
    assert decision.scoring_version == SCORING_VERSION
    assert decision.buying_intent.buying_intent_score >= 0
    assert decision.psychology.buyer_motivation
    assert decision.objections
    assert decision.offer.primary_offer
    assert decision.trust.case_studies or decision.trust.portfolio_items
    assert decision.proposal.proposal_outline
    assert decision.meeting_coach.discovery_questions
    assert decision.reply_intelligence
    assert decision.memory.relationship_timeline is not None
    assert decision.score.deal_probability >= 0
    assert decision.evidence_chain


def test_pipeline_deterministic() -> None:
    item = _item(company_id=uuid4())
    # freeze company id by rebuilding with same id
    fixed = _item(
        company_id=item.company_id,
        company_name=item.company_name,
        opportunity_score=item.opportunity_score,
        probability=item.probability,
        funding_days_ago=item.funding_days_ago,
        hiring_count=item.hiring_count,
        pains=list(item.pains),
        signals=list(item.signals),
        replies=list(item.replies),
        emails=list(item.emails),
        recommended_service=item.recommended_service,
        technologies=list(item.technologies),
        decision_makers=list(item.decision_makers),
        priority_grade=item.priority_grade,
        industry=item.industry,
        employee_count=item.employee_count,
        vendors=list(item.vendors),
    )
    a = SalesIntelligencePipeline().process(fixed)
    b = SalesIntelligencePipeline().process(fixed)
    assert a.buying_intent.buying_intent_score == b.buying_intent.buying_intent_score
    assert a.offer.primary_offer == b.offer.primary_offer
    assert a.score.deal_probability == b.score.deal_probability
    assert a.buying_intent.buying_stage == b.buying_intent.buying_stage


def test_service_evaluate_many() -> None:
    service = SalesIntelligenceService()
    items = [_item(company_name=f"Co {i}") for i in range(5)]
    results = service.evaluate_many(items)
    assert len(results) == 5
    assert all(r.scoring_version == SCORING_VERSION for r in results)


def test_cold_account_still_scores() -> None:
    decision = SalesIntelligencePipeline().process(
        _item(
            opportunity_score=5,
            probability=0,
            funding_days_ago=None,
            hiring_count=0,
            pains=[],
            signals=[],
            replies=[],
            emails=[],
            recommended_service=None,
            priority_grade="D",
        )
    )
    assert decision.buying_intent.buying_intent_score >= 0
    assert decision.offer.primary_offer
    assert decision.score.close_probability >= 0
