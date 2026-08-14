from uuid import uuid4

from autonomous_sales_agent.followup.engine import FollowUpIntelligenceEngine
from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, FollowUpChannel, FollowUpConfig


def _base(**overrides: object) -> AutonomousSalesAgentInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Follow Co",
        "email_sent": True,
        "days_since_last_touch": 0,
    }
    payload.update(overrides)
    return AutonomousSalesAgentInput.model_validate(payload)


def test_followup_day_boundaries() -> None:
    eng = FollowUpIntelligenceEngine()
    assert eng.recommend(_base(days_since_last_touch=1)).due is False
    assert eng.recommend(_base(days_since_last_touch=2)).channel == FollowUpChannel.EMAIL_FOLLOW_UP
    assert eng.recommend(_base(days_since_last_touch=4)).channel == FollowUpChannel.EMAIL_FOLLOW_UP
    assert eng.recommend(_base(days_since_last_touch=5)).channel == FollowUpChannel.VALUE_EMAIL
    assert eng.recommend(_base(days_since_last_touch=7)).channel == FollowUpChannel.VALUE_EMAIL
    assert eng.recommend(_base(days_since_last_touch=8)).channel == FollowUpChannel.WHATSAPP
    assert eng.recommend(_base(days_since_last_touch=11)).channel == FollowUpChannel.WHATSAPP
    assert eng.recommend(_base(days_since_last_touch=12)).channel == FollowUpChannel.FINAL_EMAIL
    assert eng.recommend(_base(days_since_last_touch=19)).channel == FollowUpChannel.FINAL_EMAIL
    assert eng.recommend(_base(days_since_last_touch=20)).channel == FollowUpChannel.ARCHIVE


def test_followup_custom_archive_earlier() -> None:
    cfg = FollowUpConfig(archive_days=6)
    rec = FollowUpIntelligenceEngine().recommend(_base(days_since_last_touch=6, follow_up_config=cfg))
    assert rec.channel == FollowUpChannel.ARCHIVE
