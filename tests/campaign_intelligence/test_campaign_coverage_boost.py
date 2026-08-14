from datetime import UTC, datetime
from uuid import uuid4

import pytest

from campaign_intelligence import api as campaign_api
from campaign_intelligence import metrics as campaign_metrics
from campaign_intelligence import repository as campaign_repo
from campaign_intelligence.approval.workflow import ApprovalWorkflow
from campaign_intelligence.metrics.timing import CampaignTimer
from campaign_intelligence.models.types import CampaignStatus, ChannelKind, ScheduleRules
from campaign_intelligence.planner.campaign_planner import CampaignPlanner
from campaign_intelligence.planner.message_selector import MessageSelector
from campaign_intelligence.scheduler.rules import ScheduleEngine
from campaign_intelligence.services.campaign import CampaignIntelligenceService
from tests.campaign_intelligence.test_campaign_planner import make_input


def test_stub_imports() -> None:
    assert campaign_api.__all__ == []
    assert campaign_repo.CampaignRepositoryProtocol
    assert campaign_metrics.CampaignTimer


def test_timer_and_workflow_edges() -> None:
    result, ms = CampaignTimer().time_call(lambda: 42)
    assert result == 42
    assert ms >= 0
    workflow = ApprovalWorkflow()
    assert workflow.can_transition(CampaignStatus.APPROVED, CampaignStatus.APPROVED)
    with pytest.raises(ValueError):
        workflow.transition(CampaignStatus.COMPLETED, CampaignStatus.APPROVED)
    assert workflow.schedule(CampaignStatus.APPROVED) == CampaignStatus.SCHEDULED
    assert workflow.schedule(CampaignStatus.NEEDS_REVIEW) == CampaignStatus.SCHEDULED


def test_scheduler_holiday_and_outside_hours() -> None:
    engine = ScheduleEngine(holidays={"2026-07-04"})
    rules = ScheduleRules(timezone="Invalid/Zone", business_hours_start=9, business_hours_end=17)
    early = datetime(2026, 7, 6, 6, 0, tzinfo=UTC)  # Monday before hours
    slot = engine.next_send_window(rules=rules, from_time=early, delay_hours=0)
    assert slot.hour >= 9
    holiday = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
    moved = engine.next_send_window(rules=rules, from_time=holiday, delay_hours=0)
    assert moved.date().isoformat() != "2026-07-04"
    late = datetime(2026, 7, 6, 20, 0, tzinfo=UTC)
    next_day = engine.next_send_window(rules=rules, from_time=late, delay_hours=0)
    assert next_day.hour == 9


def test_message_selector_fallbacks_and_enterprise() -> None:
    selector = MessageSelector()
    style = selector.preferred_style(
        buyer_persona="VP Sales",
        industry="Manufacturing",
        company_size="Enterprise 5000+",
        recommended_service="AI Agents platform",
        package_styles=["enterprise", "professional"],
    )
    assert style == "enterprise"
    draft, reason = selector.select_draft(
        sales_package={"drafts": [{"kind": "email", "style": "professional", "title": "x", "body": "y"}]},
        channel=ChannelKind.EMAIL,
        style="missing",
    )
    assert draft["kind"] == "email"
    assert "Selected" in reason or "No matching" in reason
    missing, missing_reason = selector.select_draft(
        sales_package={},
        channel=ChannelKind.WHATSAPP_BUSINESS,
        style="friendly",
        follow_up_index=0,
    )
    assert "Insufficient" in missing["body"]
    assert "placeholder" in missing_reason.lower() or "No matching" in missing_reason


def test_planner_channel_and_priority_branches() -> None:
    planner = CampaignPlanner()
    high = planner.plan(
        make_input(
            opportunity_score=90.0,
            opportunity_urgency=90.0,
            buyer_persona="Founder",
            verification={"overall_readiness": 40.0},
            decision_discovery={
                "best_outreach_sequence": [{"channel_kind": "linkedin_company"}],
                "buyer_match_confidence": 60.0,
                "primary_decision_maker": {"name": "A", "role": "CEO", "confidence": 70},
            },
        )
    )
    assert high.priority.value in {"critical", "high"}
    assert high.follow_up_count >= 1

    low = planner.plan(
        make_input(
            opportunity_score=40.0,
            opportunity_urgency=10.0,
            buyer_persona="Marketing Head",
            sales_package={"id": "not-a-uuid", "style_variants": [], "drafts": [], "quality_scores": {}},
            verification={"overall_readiness": 60.0},
        )
    )
    assert low.priority.value in {"low", "medium"}
    assert low.sales_package_id is None

    service = CampaignIntelligenceService()
    plan = service.create_plan(make_input())
    reviewed = service.mark_needs_review(plan)
    assert reviewed.status == CampaignStatus.NEEDS_REVIEW
