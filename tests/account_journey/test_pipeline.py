from uuid import uuid4

from account_journey import AccountJourneyPipeline
from account_journey.models.types import AccountJourneyInput, FollowUpChannel


def test_pipeline_deterministic() -> None:
    item = AccountJourneyInput(
        company_id=uuid4(),
        company_name="Det Co",
        emailed=True,
        opened=True,
        buying_intent=66,
        probability=55,
        decision_makers=[{"name": "Pat", "title": "CTO"}],
    )
    a = AccountJourneyPipeline().process(item)
    b = AccountJourneyPipeline().process(item)
    assert a.stage == b.stage
    assert a.engagement.overall_engagement == b.engagement.overall_engagement
    assert a.health.category == b.health.category
    assert a.follow_up.channel == b.follow_up.channel


def test_pipeline_adaptive_sequence_present() -> None:
    d = AccountJourneyPipeline().process(
        AccountJourneyInput(company_id=uuid4(), company_name="Seq", emailed=True, no_reply_days=2)
    )
    channels = {s.channel for s in d.multi_touch.steps}
    assert FollowUpChannel.FOLLOW_UP_EMAIL in channels or FollowUpChannel.WHATSAPP in channels or FollowUpChannel.REMINDER in channels


def test_pipeline_evidence_backed() -> None:
    d = AccountJourneyPipeline().process(AccountJourneyInput(company_id=uuid4(), company_name="E"))
    assert any(e.startswith("scoring_version:") for e in d.evidence_chain)
    assert d.outreach.evidence
    assert d.engagement.evidence
