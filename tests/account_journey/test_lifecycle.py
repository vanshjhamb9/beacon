from uuid import uuid4

from account_journey import AccountJourneyPipeline
from account_journey.models.types import AccountJourneyInput, JourneyStage


def test_lifecycle_discovered_to_won_path_markers() -> None:
    pipeline = AccountJourneyPipeline()
    stages = []
    for kwargs in [
        {"probability": 10},
        {"probability": 50},
        {"enriched": True, "probability": 50},
        {"has_decision_makers": True, "decision_makers": [{"name": "A", "title": "CEO"}]},
        {"outreach_ready": True, "has_decision_makers": True, "decision_makers": [{"name": "A"}]},
        {"campaign_active": True},
        {"emailed": True},
        {"emailed": True, "opened": True},
        {"emailed": True, "clicked": True},
        {"replied": True, "reply_text": "interested"},
        {"meeting_scheduled": True},
        {"proposal_requested": True},
        {"negotiation": True},
        {"won": True},
    ]:
        d = pipeline.process(AccountJourneyInput(company_id=uuid4(), company_name="L", **kwargs))
        stages.append(d.stage)
    assert JourneyStage.DISCOVERED in stages or JourneyStage.QUALIFIED in stages
    assert JourneyStage.WON in stages
    assert JourneyStage.MEETING_SCHEDULED in stages


def test_dormant_then_reactivated() -> None:
    pipeline = AccountJourneyPipeline()
    dormant = pipeline.process(AccountJourneyInput(company_id=uuid4(), company_name="D", emailed=True, dormant_days=30))
    reactivated = pipeline.process(AccountJourneyInput(company_id=uuid4(), company_name="R", reactivated=True))
    assert dormant.stage == JourneyStage.DORMANT
    assert reactivated.stage == JourneyStage.REACTIVATED
    assert reactivated.health.category.value == "recovered"
