from uuid import uuid4

from autonomous_sales_agent.brief.engine import MorningBriefEngine
from autonomous_sales_agent.followup.engine import FollowUpIntelligenceEngine
from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, NextActionKind, NextBestAction
from autonomous_sales_agent.queue.engine import FounderWorkQueueEngine
from autonomous_sales_agent.workflow.engine import SalesWorkflowEngine


def test_morning_brief_contains_only_required_sections() -> None:
    item = AutonomousSalesAgentInput(
        company_id=uuid4(),
        company_name="Brief Co",
        buying_intent_score=88,
        priority_grade="A+",
        email_sent=True,
        days_since_last_touch=9,
        meetings_today=[{"company_name": "Brief Co", "summary": "Discovery"}],
        high_intent_replies=[{"company_name": "Brief Co", "summary": "Interested"}],
        pipeline_value=42000,
    )
    stage = SalesWorkflowEngine().infer_stage(item)
    follow = FollowUpIntelligenceEngine().recommend(item)
    nba = NextBestAction(
        action=NextActionKind.SEND_FOLLOW_UP,
        confidence=84,
        reason="Follow up due",
        evidence=["days:9"],
        expected_impact="Re-engage",
    )
    work = FounderWorkQueueEngine().build(item, stage=stage, next_action=nba)
    brief = MorningBriefEngine().generate(item, work_queue=work, follow_up=follow, next_action=nba)
    keys = set(brief.model_dump().keys())
    assert keys == {
        "priorities",
        "expected_meetings",
        "expected_replies",
        "high_risk_deals",
        "companies_requiring_attention",
        "revenue_forecast",
        "follow_ups_due",
        "evidence",
    }
    assert brief.expected_meetings
    assert brief.follow_ups_due
    assert brief.revenue_forecast == 42000
