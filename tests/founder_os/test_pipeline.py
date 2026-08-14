from datetime import UTC, datetime
from uuid import uuid4

from founder_os import FounderOsPipeline, FounderOsInput, FounderOsService


def _data() -> FounderOsInput:
    cid = uuid4()
    return FounderOsInput(
        new_companies_found=5,
        new_buying_signals=10,
        qualified_companies=20,
        sales_ready_accounts=8,
        a_plus_opportunities=3,
        campaigns_waiting_approval=2,
        replies_waiting=1,
        meetings_today=1,
        proposals_pending=1,
        estimated_pipeline=250_000,
        expected_revenue=60_000,
        won_opportunities=2,
        lost_opportunities=1,
        industry_wins={"SaaS": 3, "Fintech": 1},
        service_wins={"Automation": 2},
        outreach_style_wins={"funding": 3, "hiring": 0},
        contacted_count=20,
        replied_count=6,
        meeting_count=3,
        proposal_count=2,
        average_deal_size=40_000,
        top_companies=[
            {
                "company_id": str(cid),
                "company_name": "Northwind",
                "priority_grade": "A",
                "recommended_service": "Automation",
                "expected_budget": "$20k–$45k",
                "probability": 70,
                "why_today": "Hiring ops roles",
                "evidence": ["hiring_count:5"],
                "proceed_to_campaign": True,
            }
        ],
        pending_campaigns=[{"id": str(uuid4()), "company_id": str(cid), "company_name": "Northwind", "status": "needs_review"}],
        meetings=[
            {
                "id": str(uuid4()),
                "company_id": str(cid),
                "company_name": "Northwind",
                "scheduled_at": datetime.now(UTC).isoformat(),
                "recommended_service": "Automation",
                "pain_points": ["manual workflows"],
            }
        ],
        proposal_candidates=[
            {
                "company_id": str(cid),
                "company_name": "Northwind",
                "recommended_service": "Automation",
                "budget_range": "$20k–$45k",
            }
        ],
        work_queue_items=[
            {
                "id": str(uuid4()),
                "company_id": str(cid),
                "company_name": "Northwind",
                "priority_grade": "A",
                "recommended_service": "Automation",
                "status": "pending",
            }
        ],
        timeline_seeds=[
            {
                "company_id": str(cid),
                "company_name": "Northwind",
                "stage": "campaign",
                "summary": "Campaign created",
                "evidence": ["status:needs_review"],
            }
        ],
        now=datetime.now(UTC),
    )


def test_pipeline_composes_full_os_pack() -> None:
    decision = FounderOsPipeline().process(_data())
    assert decision.brief.executive_summary
    assert decision.command_center.expected_revenue == 60_000
    assert decision.assistant.contacts
    assert decision.tasks
    assert decision.kpis.reply_rate >= 0
    assert decision.proposals
    assert decision.meeting_packs
    assert decision.timeline_events
    assert decision.recommendations
    assert decision.scoring_version == "fos-v1"


def test_service_facade_and_analytics() -> None:
    service = FounderOsService()
    decision = service.evaluate(_data())
    assert decision.brief.a_plus_opportunities == 3
    event = service.track_brief_view()
    assert event.action == "view_daily_brief"
