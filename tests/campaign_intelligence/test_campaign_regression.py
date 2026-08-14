from campaign_intelligence.channels.catalog import all_channels
from campaign_intelligence.models.types import CampaignStatus
from tests.campaign_intelligence.test_campaign_planner import make_input
from campaign_intelligence import CampaignPlanner


def test_no_provider_delivery_flags() -> None:
    plan = CampaignPlanner().plan(make_input())
    assert plan.quality.get("delivery_enabled") is False
    assert plan.plan_payload["schedule"]["delivery_enabled"] is False
    assert all(not channel.delivery_ready for channel in all_channels())
    blob = (plan.channel_choice_reason + plan.timing_reason + str(plan.plan_payload)).lower()
    assert "message sent" not in blob
    assert "delivery remains disabled" in blob or "delivery_enabled': false" in blob or "delivery_enabled\": false" in blob
    assert plan.status == CampaignStatus.NEEDS_REVIEW


def test_plan_exposes_quality_reasons() -> None:
    plan = CampaignPlanner().plan(make_input())
    assert plan.channel_choice_reason
    assert plan.timing_reason
    assert plan.message_selection_reason
    assert plan.evidence
    assert plan.expected_confidence > 0
