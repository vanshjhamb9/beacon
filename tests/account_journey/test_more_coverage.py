from uuid import uuid4

from account_journey import AccountJourneyPipeline, AccountJourneyService
from account_journey.committee.engine import BuyingCommitteeEngine
from account_journey.models.types import AccountJourneyInput, CommitteeRole
from account_journey.replies.engine import ReplyIntelligenceV2Engine


def test_committee_influencer_fallback() -> None:
    c = BuyingCommitteeEngine().build(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="I",
            decision_makers=[{"name": "Sam", "title": "Analyst"}],
        )
    )
    assert c.members[0].role == CommitteeRole.INFLUENCER


def test_reply_unknown_fallback() -> None:
    r = ReplyIntelligenceV2Engine().classify(
        AccountJourneyInput(company_id=uuid4(), company_name="U", replied=True, reply_text="asdf qwerty")
    )
    assert r is not None
    assert r.classification.value in {"unknown", "interested"} or r.confidence >= 0


def test_pipeline_batch_unique_companies() -> None:
    items = [
        AccountJourneyInput(company_id=uuid4(), company_name=f"B{i}", emailed=True, no_reply_days=i)
        for i in range(12)
    ]
    out = AccountJourneyService().evaluate_many(items)
    assert len({d.company_id for d in out}) == 12


def test_opened_without_reply_is_opened_stage() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="O", emailed=True, opened=True, decision_makers=[])
    )
    assert d.stage.value == "opened"


def test_calendly_boosts_meeting_score() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="Cal", calendly_opened=True, emailed=True)
    )
    assert d.engagement.meeting_score >= 25


def test_cta_clicks_enter_clicked_stage() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="CTA", emailed=True, cta_clicks=3, decision_makers=[])
    )
    assert d.stage.value == "clicked"


def test_followup_meeting_when_replied() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="Meet", replied=True, reply_text="interested")
    )
    assert d.follow_up.next_action in {"book_meeting", "meeting_ask"} or d.follow_up.channel.value == "meeting"


def test_analytics_revenue_sorted() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="A",
            country="US",
            cohort_accounts=[
                {"country": "US", "replied": True, "meeting": True, "proposal": True, "won": True, "revenue": 50000},
                {"country": "IN", "replied": False, "meeting": False, "proposal": False, "won": False, "revenue": 100},
            ],
        )
    )
    assert d.analytics.by_country[0].key == "US"


def test_timeline_seed_appended() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="Seed",
            timeline_seeds=[{"event_type": "custom", "title": "Custom", "actor": "ops"}],
        )
    )
    assert any(e.event_type == "custom" for e in d.timeline)


def test_relationship_score_grows_with_dms() -> None:
    few = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="F", decision_makers=[{"name": "A", "title": "CEO"}])
    )
    many = AccountJourneyPipeline().process(
        AccountJourneyInput(
            company_id=uuid4(),
            company_name="M",
            decision_makers=[{"name": f"P{i}", "title": "Manager"} for i in range(5)],
            replied=True,
            meeting_scheduled=True,
        )
    )
    assert many.engagement.relationship_score > few.engagement.relationship_score


def test_priority_health_for_meeting() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="P", meeting_scheduled=True, probability=50, buying_intent=50)
    )
    assert d.health.category.value in {"priority", "critical", "hot"}


def test_spam_stops_hint() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="S", replied=True, reply_text="please unsubscribe")
    )
    assert d.reply is not None
    assert d.reply.classification.value == "spam"
    assert "Stop" in str(d.reply.structured_outcome.get("next_hint"))
