from uuid import uuid4

import pytest

from account_journey import SCORING_VERSION, AccountJourneyPipeline, AccountJourneyService
from account_journey.committee.engine import BuyingCommitteeEngine
from account_journey.engagement.engine import EngagementScoringEngine
from account_journey.followup.engine import FollowUpPlannerEngine
from account_journey.health.engine import AccountHealthEngine
from account_journey.journey.engine import AccountJourneyEngine
from account_journey.models.types import (
    AccountHealthCategory,
    AccountJourneyInput,
    CommitteeRole,
    FollowUpChannel,
    JourneyStage,
    ReplyClass,
)
from account_journey.orchestration.engine import MultiTouchOrchestrator
from account_journey.outreach.engine import OutreachIntelligenceEngine
from account_journey.replies.engine import ReplyIntelligenceV2Engine
from account_journey.timeline.engine import AccountTimelineEngine


def _item(**overrides: object) -> AccountJourneyInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Orbit Labs",
        "industry": "SaaS",
        "country": "US",
        "company_size": "51-200",
        "technologies": ["Python"],
        "service": "AI Automation",
        "campaign_name": "Q3",
        "probability": 65,
        "buying_intent": 70,
        "decision_makers": [{"name": "Alex", "title": "CEO"}],
    }
    payload.update(overrides)
    return AccountJourneyInput.model_validate(payload)


def test_scoring_version() -> None:
    assert SCORING_VERSION == "goi-v1"


@pytest.mark.parametrize(
    ("kwargs", "stage"),
    [
        ({"decision_makers": [], "has_decision_makers": False}, JourneyStage.QUALIFIED),
        ({"qualified": False, "probability": 10, "decision_makers": [], "has_decision_makers": False}, JourneyStage.DISCOVERED),
        ({"enriched": True, "qualified": True, "has_decision_makers": False, "decision_makers": []}, JourneyStage.ENRICHED),
        ({"has_decision_makers": True}, JourneyStage.DECISION_MAKERS),
        ({"outreach_ready": True, "has_decision_makers": True}, JourneyStage.OUTREACH_READY),
        ({"campaign_active": True}, JourneyStage.CAMPAIGN_ACTIVE),
        ({"emailed": True}, JourneyStage.CONTACTED),
        ({"emailed": True, "opened": True}, JourneyStage.OPENED),
        ({"emailed": True, "clicked": True}, JourneyStage.CLICKED),
        ({"replied": True}, JourneyStage.REPLIED),
        ({"meeting_scheduled": True}, JourneyStage.MEETING_SCHEDULED),
        ({"proposal_requested": True}, JourneyStage.PROPOSAL_REQUESTED),
        ({"negotiation": True}, JourneyStage.NEGOTIATION),
        ({"won": True}, JourneyStage.WON),
        ({"lost": True}, JourneyStage.LOST),
        ({"dormant_days": 25, "emailed": True}, JourneyStage.DORMANT),
        ({"reactivated": True}, JourneyStage.REACTIVATED),
    ],
)
def test_journey_stages(kwargs: dict, stage: JourneyStage) -> None:
    assert AccountJourneyEngine().infer_stage(_item(**kwargs)) == stage


def test_transitions_append_only_fields() -> None:
    stage = JourneyStage.CONTACTED
    t = AccountJourneyEngine().build_transitions(_item(emailed=True), stage)[0]
    assert t.to_stage == stage
    assert t.reason
    assert t.evidence
    assert t.actor == "system"
    assert t.timestamp is not None


def test_outreach_signals() -> None:
    out = OutreachIntelligenceEngine().score(
        _item(
            emailed=True,
            whatsapp_sent=True,
            replied=True,
            cta_clicks=2,
            video_watched=True,
            calendly_opened=True,
            calendar_booked=True,
            meeting_scheduled=True,
        )
    )
    kinds = {s.kind for s in out.signals}
    assert {"email", "whatsapp", "reply", "cta_clicks", "video_watched", "calendly_opened", "calendar_booked", "meeting"} <= kinds
    assert out.positive_score > out.negative_score


def test_outreach_ghosting() -> None:
    out = OutreachIntelligenceEngine().score(_item(emailed=True, no_reply_days=10, opened=False, replied=False))
    assert out.ghosting is True
    assert any(s.kind == "ghosting" for s in out.signals)


def test_engagement_scores_bounds() -> None:
    outreach = OutreachIntelligenceEngine().score(_item(opened=True, replied=True, meeting_scheduled=True))
    e = EngagementScoringEngine().score(_item(opened=True, replied=True, meeting_scheduled=True, buying_intent=80), outreach=outreach)
    for val in [e.open_score, e.reply_score, e.intent_score, e.meeting_score, e.relationship_score, e.account_temperature, e.overall_engagement]:
        assert 0 <= val <= 100


def test_multi_touch_adaptive_not_fixed() -> None:
    cold = _item(emailed=True, buying_intent=20, probability=20)
    hot = _item(emailed=True, replied=True, buying_intent=90, probability=90, meeting_scheduled=False)
    o1 = OutreachIntelligenceEngine().score(cold)
    o2 = OutreachIntelligenceEngine().score(hot)
    e1 = EngagementScoringEngine().score(cold, outreach=o1)
    e2 = EngagementScoringEngine().score(hot, outreach=o2)
    p1 = MultiTouchOrchestrator().plan(cold, engagement=e1, outreach=o1)
    p2 = MultiTouchOrchestrator().plan(hot, engagement=e2, outreach=o2)
    assert p1.adaptive is True
    assert "fixed_intervals:false" in p1.evidence
    delays1 = [s.delay_hours for s in p1.steps if s.channel == FollowUpChannel.FOLLOW_UP_EMAIL]
    delays2 = [s.delay_hours for s in p2.steps if s.channel != FollowUpChannel.WAIT]
    assert delays1 or p1.steps
    assert delays2


def test_multi_touch_requires_founder_approval() -> None:
    item = _item()
    outreach = OutreachIntelligenceEngine().score(item)
    engagement = EngagementScoringEngine().score(item, outreach=outreach)
    plan = MultiTouchOrchestrator().plan(item, engagement=engagement, outreach=outreach)
    assert all(s.requires_founder_approval or s.channel == FollowUpChannel.WAIT for s in plan.steps)


def test_health_categories() -> None:
    eng = AccountHealthEngine()
    outreach = OutreachIntelligenceEngine()
    scoring = EngagementScoringEngine()

    def health(item: AccountJourneyInput) -> AccountHealthCategory:
        stage = AccountJourneyEngine().infer_stage(item)
        o = outreach.score(item)
        e = scoring.score(item, outreach=o)
        return eng.classify(item, stage=stage, engagement=e).category

    assert health(_item(dormant_days=25, emailed=True)) == AccountHealthCategory.DORMANT
    assert health(_item(reactivated=True)) == AccountHealthCategory.RECOVERED
    assert health(_item(negotiation=True)) == AccountHealthCategory.CRITICAL
    assert health(_item(replied=True, buying_intent=90, probability=90)) in {
        AccountHealthCategory.HOT,
        AccountHealthCategory.CRITICAL,
        AccountHealthCategory.PRIORITY,
    }


def test_buying_committee_roles() -> None:
    committee = BuyingCommitteeEngine().build(
        _item(
            decision_makers=[
                {"name": "A", "title": "CEO"},
                {"name": "B", "title": "CTO"},
                {"name": "C", "title": "Legal Counsel"},
                {"name": "D", "title": "Procurement Lead"},
                {"name": "E", "title": "COO"},
                {"name": "F", "title": "Growth Champion"},
            ]
        )
    )
    roles = {m.role for m in committee.members}
    assert CommitteeRole.ECONOMIC_BUYER in roles
    assert CommitteeRole.TECHNICAL_BUYER in roles
    assert committee.coverage > 0
    assert isinstance(committee.missing_roles, list)


def test_followup_planner_founder_gate() -> None:
    d = AccountJourneyPipeline().process(_item(emailed=True, no_reply_days=3))
    assert d.follow_up.requires_founder_approval is True
    assert d.follow_up.channel != FollowUpChannel.WAIT or d.follow_up.next_action


def test_reply_intelligence_classes() -> None:
    eng = ReplyIntelligenceV2Engine()
    cases = [
        ("Let's meet next week", ReplyClass.MEETING_REQUESTED),
        ("Please send a proposal", ReplyClass.NEED_PROPOSAL),
        ("Budget is tight this quarter", ReplyClass.BUDGET_CONCERN),
        ("Not now, revisit later", ReplyClass.NOT_NOW),
        ("Timing is bad, next quarter", ReplyClass.TIMING_CONCERN),
        ("Already using a vendor", ReplyClass.COMPETITOR),
        ("Wrong person, forward to ops", ReplyClass.WRONG_CONTACT),
        ("Unsubscribe / spam", ReplyClass.SPAM),
        ("Interested, tell me more", ReplyClass.INTERESTED),
    ]
    for text, expected in cases:
        result = eng.classify(_item(replied=True, reply_text=text))
        assert result is not None
        assert result.classification == expected
        assert result.structured_outcome


def test_timeline_unified_events() -> None:
    events = AccountTimelineEngine().build(
        _item(
            has_decision_makers=True,
            emailed=True,
            whatsapp_sent=True,
            replied=True,
            meeting_scheduled=True,
            founder_notes=["Good call"],
            campaign_active=True,
        )
    )
    types = {e.event_type for e in events}
    assert {"discovery", "research", "decision_makers", "email", "whatsapp", "reply", "meeting", "founder_note", "campaign_change", "forecast_update"} <= types


def test_pipeline_full() -> None:
    d = AccountJourneyService().evaluate(_item(emailed=True, opened=True, replied=True, reply_text="Interested"))
    assert d.stage == JourneyStage.REPLIED
    assert d.engagement
    assert d.health
    assert d.buying_committee
    assert d.follow_up
    assert d.multi_touch
    assert d.analytics
    assert d.reply
    assert d.timeline
    assert "compose_only:true" in d.evidence_chain


def test_evaluate_many() -> None:
    out = AccountJourneyService().evaluate_many([_item(company_name=f"C{i}") for i in range(5)])
    assert len(out) == 5


def test_classify_reply_wrapper() -> None:
    result = AccountJourneyService().classify_reply("Need a proposal please")
    assert result is not None
    assert result.classification == ReplyClass.NEED_PROPOSAL
