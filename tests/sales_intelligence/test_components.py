from uuid import uuid4

from sales_intelligence.intent.engine import BuyingIntentEngine
from sales_intelligence.meeting.engine import MeetingCoachEngine
from sales_intelligence.memory.engine import SalesMemoryEngine
from sales_intelligence.models.types import (
    OfferType,
    ReplyClass,
    SalesIntelligenceInput,
    UrgencyLevel,
)
from sales_intelligence.objections.engine import ObjectionPredictionEngine
from sales_intelligence.offers.engine import OfferRecommendationEngine
from sales_intelligence.proposal.engine import ProposalIntelligenceEngine
from sales_intelligence.psychology.engine import PsychologyEngine
from sales_intelligence.reply.engine import ReplyIntelligenceEngine
from sales_intelligence.score.engine import SalesScoreEngine
from sales_intelligence.trust.engine import TrustBuilderEngine


def _item(**overrides: object) -> SalesIntelligenceInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Nova Health",
        "industry": "Healthcare",
        "country": "United States",
        "employee_count": 120,
        "funding_stage": "series_a",
        "funding_days_ago": 21,
        "revenue_band": "mid",
        "technologies": ["Python", "Zapier", "LLM"],
        "pains": ["manual workflows", "high support cost", "compliance"],
        "goals": ["scale ops", "automation"],
        "signals": ["funding", "hiring", "support growth"],
        "hiring_roles": ["Ops Manager", "Support Lead"],
        "hiring_count": 6,
        "decision_makers": [{"name": "Ava Chen", "title": "COO", "email": "ava@nova.example"}],
        "recommended_service": "AI Automation",
        "expected_budget": "$25k–$45k",
        "opportunity_score": 86,
        "priority_grade": "A+",
        "probability": 72,
        "replies": [{"id": "r1", "subject": "Re: intro", "body": "Interested — can we schedule a call?"}],
        "emails": [{"subject": "Intro", "body": "Quick note", "sent_at": "2026-07-01T10:00:00+00:00"}],
        "meetings": [],
        "proposals": [],
        "objections_seen": ["budget"],
        "notes": ["Warm intro via investor"],
        "outcomes": [],
        "vendors": ["Zendesk"],
    }
    payload.update(overrides)
    return SalesIntelligenceInput(**payload)  # type: ignore[arg-type]


def test_buying_intent_high_for_hot_account() -> None:
    result = BuyingIntentEngine().analyze(_item())
    assert result.buying_intent_score >= 70
    assert result.urgency in {UrgencyLevel.HIGH, UrgencyLevel.CRITICAL, UrgencyLevel.MEDIUM}
    assert result.decision_window_days in {14, 30, 60}
    assert result.evidence_chain
    assert 0 <= result.buying_confidence <= 100


def test_buying_intent_low_without_signals() -> None:
    result = BuyingIntentEngine().analyze(
        _item(
            opportunity_score=10,
            probability=5,
            funding_days_ago=None,
            hiring_count=0,
            pains=[],
            signals=[],
            replies=[],
            priority_grade="C",
        )
    )
    assert result.buying_intent_score < 55


def test_psychology_profiles_buyer() -> None:
    profile = PsychologyEngine().analyze(_item())
    assert profile.buyer_motivation
    assert profile.preferred_communication_style
    assert 0 <= profile.automation_readiness <= 100
    assert 0 <= profile.pain_intensity <= 100
    assert profile.evidence


def test_objection_prediction_covers_core_types() -> None:
    objs = ObjectionPredictionEngine().predict(_item())
    assert objs
    names = {o.objection.value for o in objs}
    assert "Budget" in names or "ROI" in names
    assert all(o.suggested_response and o.evidence for o in objs)
    assert objs == sorted(objs, key=lambda o: (-o.likelihood, o.objection.value))


def test_offer_recommendation_ranks_primary() -> None:
    offer = OfferRecommendationEngine().recommend(_item())
    assert offer.primary_offer
    assert offer.expected_value
    assert offer.ranking
    assert offer.ranking[0]["offer"] == offer.primary_offer.value


def test_trust_builder_evidence_based() -> None:
    trust = TrustBuilderEngine().build(_item(), primary_offer=OfferType.AI_AUTOMATION)
    assert trust.case_studies or trust.portfolio_items
    assert trust.industries_served
    assert trust.technology_stack


def test_proposal_intelligence_structure() -> None:
    proposal = ProposalIntelligenceEngine().generate(_item(), primary_offer=OfferType.AI_AUTOMATION)
    assert proposal.proposal_outline
    assert proposal.scope
    assert proposal.timeline
    assert proposal.deliverables
    assert proposal.architecture
    assert proposal.budget_range
    assert proposal.roi_estimate
    assert proposal.implementation_plan
    assert proposal.risk_assessment


def test_meeting_coach_pack() -> None:
    item = _item()
    intent = BuyingIntentEngine().analyze(item)
    psych = PsychologyEngine().analyze(item)
    objs = ObjectionPredictionEngine().predict(item)
    pack = MeetingCoachEngine().coach(item, intent=intent, psychology=psych, objections=objs)
    assert pack.company_summary
    assert pack.discovery_questions
    assert pack.closing_strategy
    assert pack.follow_up_plan


def test_reply_intelligence_classifications() -> None:
    engine = ReplyIntelligenceEngine()
    assert engine.classify("Sounds good, interested").classification == ReplyClass.INTERESTED
    assert engine.classify("Please send a proposal and pricing").classification == ReplyClass.NEED_PROPOSAL
    assert engine.classify("Can we book a meeting next week?").classification == ReplyClass.NEED_MEETING
    assert engine.classify("How does the API integrate?").classification == ReplyClass.TECHNICAL_QUESTION
    assert engine.classify("This is too expensive for our budget").classification == ReplyClass.BUDGET_CONCERN
    assert engine.classify("Need SOC2 and security docs").classification == ReplyClass.SECURITY_CONCERN
    assert engine.classify("Maybe next quarter").classification == ReplyClass.TIMING_ISSUE
    assert engine.classify("Wrong person, talk to finance").classification == ReplyClass.WRONG_CONTACT
    assert engine.classify("Not interested, please remove").classification == ReplyClass.NOT_INTERESTED
    empty = engine.classify("")
    assert empty.classification == ReplyClass.UNKNOWN


def test_sales_memory_timeline_and_journey() -> None:
    memory = SalesMemoryEngine().build(
        _item(
            meetings=[{"title": "Discovery", "scheduled_at": "2026-07-10T15:00:00+00:00"}],
            proposals=[{"title": "MVP SOW", "status": "sent", "sent_at": "2026-07-12T12:00:00+00:00"}],
        )
    )
    assert memory.events
    assert memory.relationship_timeline
    assert any(j["stage"] == "outreach" for j in memory.buying_journey)
    assert any(j["stage"] == "engagement" and j["done"] for j in memory.buying_journey)


def test_sales_score_bounds() -> None:
    item = _item()
    intent = BuyingIntentEngine().analyze(item)
    psych = PsychologyEngine().analyze(item)
    objs = ObjectionPredictionEngine().predict(item)
    offer = OfferRecommendationEngine().recommend(item)
    score = SalesScoreEngine().score(item, intent=intent, psychology=psych, objections=objs, offer=offer)
    assert 0 <= score.deal_probability <= 100
    assert 0 <= score.close_probability <= 100
    assert score.expected_deal_size
    assert score.evidence
