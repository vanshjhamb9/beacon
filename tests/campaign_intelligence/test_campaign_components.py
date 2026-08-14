from datetime import UTC, datetime

from campaign_intelligence.analytics.metrics import CampaignAnalytics
from campaign_intelligence.approval.workflow import ApprovalWorkflow
from campaign_intelligence.channels.catalog import all_channels, get_channel
from campaign_intelligence.models.types import CampaignStatus, ChannelKind, ScheduleRules
from campaign_intelligence.planner.message_selector import MessageSelector
from campaign_intelligence.scheduler.rules import ScheduleEngine


def test_channel_catalog_delivery_disabled() -> None:
    channels = all_channels()
    assert len(channels) == 6
    assert all(not channel.delivery_ready for channel in channels)
    assert get_channel(ChannelKind.EMAIL).label == "Email"


def test_approval_workflow_transitions() -> None:
    workflow = ApprovalWorkflow()
    assert workflow.can_transition(CampaignStatus.NEEDS_REVIEW, CampaignStatus.APPROVED)
    assert workflow.approve(CampaignStatus.NEEDS_REVIEW) == CampaignStatus.APPROVED
    assert workflow.pause(CampaignStatus.SCHEDULED) == CampaignStatus.PAUSED
    assert workflow.cancel(CampaignStatus.APPROVED) == CampaignStatus.CANCELLED


def test_schedule_engine_business_hours() -> None:
    engine = ScheduleEngine(holidays={"2026-07-04"})
    rules = ScheduleRules(timezone="UTC", business_hours_start=9, business_hours_end=17, working_days=[0, 1, 2, 3, 4])
    # Saturday 2026-07-18 -> should roll forward
    saturday = datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    slot = engine.next_send_window(rules=rules, from_time=saturday, delay_hours=0)
    assert slot.weekday() < 5
    times = engine.plan_step_times(rules=rules, delay_hours=[0.0, 48.0])
    assert len(times) == 2
    assert "business hours" in engine.timing_reason(rules).lower()


def test_message_selector_prefers_technical_for_cto() -> None:
    selector = MessageSelector()
    style = selector.preferred_style(
        buyer_persona="CTO",
        industry="Software",
        company_size="100",
        recommended_service="AI Automation",
        package_styles=["technical", "professional"],
    )
    assert style == "technical"
    draft, reason = selector.select_draft(
        sales_package={
            "style_variants": [
                {
                    "style": "technical",
                    "drafts": [{"kind": "email", "style": "technical", "title": "t", "body": "hi", "subject_lines": ["s"]}],
                }
            ]
        },
        channel=ChannelKind.EMAIL,
        style="technical",
    )
    assert draft["kind"] == "email"
    assert "Selected" in reason


def test_analytics_dashboard() -> None:
    metrics = CampaignAnalytics().dashboard(
        [
            {"status": "needs_review", "priority": "high", "primary_channel": "email", "expected_confidence": 70},
            {"status": "scheduled", "priority": "critical", "primary_channel": "linkedin", "expected_confidence": 90},
        ]
    )
    assert metrics["total_campaigns"] == 2
    assert metrics["delivery_enabled"] is False
    assert metrics["needs_review"] == 1
