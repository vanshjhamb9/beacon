from uuid import uuid4

from autonomous_sales_agent.meeting.engine import MeetingIntelligenceEngine
from autonomous_sales_agent.models.types import AutonomousSalesAgentInput


REQUIRED_FIELDS = [
    "company_overview",
    "decision_makers",
    "business_pains",
    "automation_opportunities",
    "likely_objections",
    "discovery_questions",
    "upsell_ideas",
    "cross_sell_ideas",
    "budget_hints",
    "technology_stack",
    "recent_activity",
    "competitive_landscape",
    "roi_talking_points",
    "meeting_agenda",
    "success_checklist",
]


def test_meeting_intelligence_required_sections() -> None:
    pack = MeetingIntelligenceEngine().prepare(
        AutonomousSalesAgentInput(
            company_id=uuid4(),
            company_name="Meet Co",
            industry="Retail",
            decision_makers=[{"name": "Sam"}],
            pains=["inventory lag"],
            technologies=["Shopify"],
            vendors=["Zendesk"],
            objections_seen=["Timing"],
            recommended_service="AI Automation",
            expected_budget="$30k",
            recent_activity=["opened email"],
        )
    )
    data = pack.model_dump()
    for field in REQUIRED_FIELDS:
        assert field in data
        assert data[field] not in (None, "", [])
