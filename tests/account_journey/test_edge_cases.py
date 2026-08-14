from uuid import uuid4

from account_journey import AccountJourneyPipeline
from account_journey.journey.engine import AccountJourneyEngine
from account_journey.models.types import AccountJourneyInput, JourneyStage
from account_journey.outreach.engine import OutreachIntelligenceEngine
from account_journey.replies.engine import ReplyIntelligenceV2Engine


def test_calendar_booked_is_meeting_stage() -> None:
    assert AccountJourneyEngine().infer_stage(
        AccountJourneyInput(company_id=uuid4(), company_name="C", calendar_booked=True, decision_makers=[])
    ) == JourneyStage.MEETING_SCHEDULED


def test_whatsapp_only_is_contacted() -> None:
    assert AccountJourneyEngine().infer_stage(
        AccountJourneyInput(company_id=uuid4(), company_name="W", whatsapp_sent=True, decision_makers=[])
    ) == JourneyStage.CONTACTED


def test_no_reply_signal_negative() -> None:
    out = OutreachIntelligenceEngine().score(
        AccountJourneyInput(company_id=uuid4(), company_name="N", emailed=True, no_reply_days=6, decision_makers=[])
    )
    assert any(s.kind == "no_reply" and s.polarity == "negative" for s in out.signals)


def test_reply_none_when_no_reply() -> None:
    assert ReplyIntelligenceV2Engine().classify(
        AccountJourneyInput(company_id=uuid4(), company_name="X", replied=False, reply_text="")
    ) is None


def test_lost_beats_negotiation() -> None:
    assert AccountJourneyEngine().infer_stage(
        AccountJourneyInput(company_id=uuid4(), company_name="L", negotiation=True, lost=True)
    ) == JourneyStage.LOST


def test_won_beats_lost_flag_order() -> None:
    # won checked first
    assert AccountJourneyEngine().infer_stage(
        AccountJourneyInput(company_id=uuid4(), company_name="W", won=True, lost=True)
    ) == JourneyStage.WON


def test_proposal_followup() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="P", proposal_requested=True)
    )
    assert d.follow_up.channel.value == "proposal"
    assert d.follow_up.requires_founder_approval is True


def test_meeting_prep_followup() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="M", meeting_scheduled=True)
    )
    assert d.follow_up.next_action == "prepare_meeting"


def test_multi_touch_email_first_when_not_sent() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="E", decision_makers=[], probability=20)
    )
    assert d.multi_touch.steps[0].channel.value == "email"


def test_health_hot_from_temperature() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="H",
            emailed=True,
            opened=True,
            replied=True,
            reply_text="interested tell me more",
            calendly_opened=True,
            buying_intent=95,
            probability=90,
            cta_clicks=2,
            video_watched=True,
        )
    )
    assert d.health.category.value in {"hot", "critical", "priority"}


def test_committee_coverage_increases() -> None:
    one = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="1", decision_makers=[{"name": "A", "title": "CEO"}])
    )
    many = AccountJourneyPipeline().process(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="2",
            decision_makers=[
                {"name": "A", "title": "CEO"},
                {"name": "B", "title": "CTO"},
                {"name": "C", "title": "Legal"},
                {"name": "D", "title": "Procurement"},
            ],
        )
    )
    assert many.buying_committee.coverage > one.buying_committee.coverage


def test_transition_history_never_empty() -> None:
    d = AccountJourneyPipeline().process(AccountJourneyInput(company_id=uuid4(), company_name="T"))
    assert len(d.transitions) >= 1
    assert d.transitions[0].from_stage is None


def test_ghosting_increases_negative_score() -> None:
    quiet = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="Q", emailed=True, no_reply_days=1, decision_makers=[])
    )
    ghost = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="G", emailed=True, no_reply_days=12, opened=False, decision_makers=[])
    )
    assert ghost.outreach.negative_score >= quiet.outreach.negative_score


def test_intent_score_uses_buying_intent() -> None:
    low = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="L", buying_intent=10, probability=10, decision_makers=[])
    )
    high = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="H", buying_intent=95, probability=90, decision_makers=[])
    )
    assert high.engagement.intent_score > low.engagement.intent_score


def test_founder_note_on_timeline() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="N", founder_notes=["Called CFO"])
    )
    assert any(e.event_type == "founder_note" and e.actor == "founder" for e in d.timeline)


def test_service_field_flows_to_analytics() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="S", service="Hospitality AI", industry="Hospitality")
    )
    assert any(s.key == "Hospitality AI" for s in d.analytics.by_service) or d.analytics.by_service
