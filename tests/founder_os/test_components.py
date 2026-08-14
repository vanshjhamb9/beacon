from datetime import UTC, datetime
from uuid import uuid4

from founder_os.assistant.engine import FounderAssistantEngine
from founder_os.brief.engine import DailyBriefEngine
from founder_os.kpi.engine import SalesKPIEngine
from founder_os.models.types import FounderOsInput, TaskKind
from founder_os.recommendations.engine import FounderRecommendationEngine
from founder_os.tasks.engine import RevenueTaskEngine
from founder_os.timeline.engine import RevenueTimelineEngine


def _input(**overrides: object) -> FounderOsInput:
    payload: dict[str, object] = {
        "new_companies_found": 12,
        "new_buying_signals": 28,
        "qualified_companies": 40,
        "sales_ready_accounts": 18,
        "a_plus_opportunities": 6,
        "campaigns_waiting_approval": 4,
        "replies_waiting": 3,
        "meetings_today": 2,
        "proposals_pending": 2,
        "estimated_pipeline": 420_000,
        "expected_revenue": 95_000,
        "lost_opportunities": 1,
        "won_opportunities": 3,
        "industry_wins": {"Healthcare": 5, "SaaS": 2},
        "service_wins": {"Custom AI": 4, "COMAI": 2},
        "outreach_style_wins": {"funding": 5, "hiring": 1},
        "contacted_count": 40,
        "replied_count": 12,
        "meeting_count": 6,
        "proposal_count": 3,
        "average_deal_size": 45_000,
        "average_sales_cycle_days": 28,
        "campaign_sends": 40,
        "campaign_replies": 12,
        "top_companies": [
            {
                "company_id": str(uuid4()),
                "company_name": "Helix Health",
                "priority_grade": "A+",
                "recommended_service": "Custom AI",
                "expected_budget": "$60k–$120k",
                "probability": 78,
                "why_today": "Funding 14 days ago",
                "why_them": "Healthcare ICP + manual workflows",
                "evidence": ["funding_days_ago:14", "industry:Healthcare"],
                "proceed_to_campaign": True,
            }
        ],
        "pending_campaigns": [
            {"id": str(uuid4()), "company_id": str(uuid4()), "company_name": "Helix Health", "status": "needs_review"}
        ],
        "pending_replies": [{"id": str(uuid4()), "company_id": str(uuid4()), "company_name": "Helix Health"}],
        "meetings": [
            {
                "id": str(uuid4()),
                "company_id": str(uuid4()),
                "company_name": "Helix Health",
                "scheduled_at": datetime.now(UTC).isoformat(),
                "recommended_service": "Custom AI",
                "pain_points": ["manual workflows"],
                "buying_signals": ["funding"],
                "decision_makers": [{"name": "Dr. Lee", "role": "CTO"}],
            }
        ],
        "proposal_candidates": [
            {
                "company_id": str(uuid4()),
                "company_name": "Helix Health",
                "recommended_service": "Custom AI",
                "budget_range": "$60k–$120k",
            }
        ],
        "website_audit_needed": [{"company_id": str(uuid4()), "company_name": "Helix Health", "evidence": ["severity:high"]}],
        "timeline_seeds": [
            {
                "company_id": str(uuid4()),
                "company_name": "Helix Health",
                "stage": "meeting",
                "summary": "Meeting scheduled",
                "evidence": ["lifecycle:meeting_scheduled"],
            }
        ],
        "now": datetime.now(UTC),
    }
    payload.update(overrides)
    return FounderOsInput(**payload)  # type: ignore[arg-type]


def test_daily_brief_has_summary_and_evidence() -> None:
    brief = DailyBriefEngine().generate(_input())
    assert brief.a_plus_opportunities == 6
    assert brief.top_performing_industry == "Healthcare"
    assert brief.top_performing_service == "Custom AI"
    assert "Pipeline" in brief.executive_summary or "pipeline" in brief.executive_summary.lower()
    assert brief.evidence


def test_assistant_answers_who_why_what() -> None:
    assistant = FounderAssistantEngine().brief(_input())
    assert assistant.contacts
    c = assistant.contacts[0]
    assert c.why_them and c.why_today and c.what_to_sell
    assert c.expected_budget and c.next_action
    assert c.evidence


def test_tasks_cover_required_kinds() -> None:
    tasks = RevenueTaskEngine().generate(_input())
    kinds = {t.kind for t in tasks}
    assert TaskKind.APPROVE_CAMPAIGN in kinds
    assert TaskKind.REPLY_NEEDED in kinds
    assert TaskKind.MEETING_TODAY in kinds
    assert TaskKind.PROPOSAL_REQUIRED in kinds
    assert all(t.reason and t.evidence for t in tasks)


def test_kpis_and_recommendations_deterministic() -> None:
    data = _input()
    kpis = SalesKPIEngine().calculate(data)
    assert 0 <= kpis.reply_rate <= 100
    assert kpis.evidence
    recs = FounderRecommendationEngine().generate(data, kpis)
    assert recs
    assert all(r.evidence for r in recs)
    # Determinism
    assert SalesKPIEngine().calculate(data).reply_rate == kpis.reply_rate


def test_timeline_immutable_flag() -> None:
    events = RevenueTimelineEngine().build_events(_input())
    assert events
    assert all(e.immutable is True for e in events)
