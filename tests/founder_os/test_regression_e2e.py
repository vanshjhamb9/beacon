from datetime import UTC, datetime
from uuid import uuid4

from founder_os import FounderOsPipeline, FounderOsInput
from founder_os.models.types import ProposalStatus, TimelineStage


def _pack() -> FounderOsInput:
    cid = uuid4()
    return FounderOsInput(
        a_plus_opportunities=2,
        campaigns_waiting_approval=3,
        replies_waiting=2,
        meetings_today=1,
        estimated_pipeline=180_000,
        expected_revenue=40_000,
        won_opportunities=4,
        industry_wins={"Healthcare": 4, "Legal": 1},
        service_wins={"Custom AI": 3},
        outreach_style_wins={"funding": 4, "hiring": 1},
        contacted_count=30,
        replied_count=10,
        meeting_count=5,
        proposal_count=3,
        average_deal_size=50_000,
        website_audit_needed=[{"company_id": str(cid), "company_name": "MedCo", "evidence": ["severity:high"]}],
        top_companies=[
            {
                "company_id": str(cid),
                "company_name": "MedCo",
                "priority_grade": "A+",
                "recommended_service": "Custom AI",
                "expected_budget": "$60k–$120k",
                "probability": 80,
                "why_today": "Why today: funding",
                "why_them": "Healthcare ICP",
                "evidence": ["industry:Healthcare"],
                "proceed_to_campaign": True,
            }
        ],
        proposal_candidates=[
            {
                "company_id": str(cid),
                "company_name": "MedCo",
                "recommended_service": "Custom AI",
                "budget_range": "$60k–$120k",
                "proposal_status": "needed",
            }
        ],
        meetings=[
            {
                "id": str(uuid4()),
                "company_id": str(cid),
                "company_name": "MedCo",
                "scheduled_at": datetime.now(UTC).isoformat(),
                "recommended_service": "Custom AI",
                "pain_points": ["old technology"],
                "decision_makers": [{"name": "Pat", "role": "CTO"}],
            }
        ],
        timeline_seeds=[
            {"company_id": str(cid), "company_name": "MedCo", "stage": "won", "summary": "Closed won", "evidence": ["deal:won"]}
        ],
        now=datetime.now(UTC),
    )


def test_regression_no_recommendation_without_evidence() -> None:
    decision = FounderOsPipeline().process(_pack())
    assert all(r.evidence for r in decision.recommendations)


def test_regression_proposal_and_meeting_packs() -> None:
    decision = FounderOsPipeline().process(_pack())
    assert decision.proposals[0].proposal_status == ProposalStatus.NEEDED
    assert decision.meeting_packs[0].discovery_questions
    assert decision.meeting_packs[0].closing_strategy


def test_regression_timeline_stages_valid() -> None:
    decision = FounderOsPipeline().process(_pack())
    assert decision.timeline_events[0].stage == TimelineStage.WON
    assert decision.timeline_events[0].immutable is True


def test_deterministic_pack() -> None:
    data = _pack()
    a = FounderOsPipeline().process(data)
    b = FounderOsPipeline().process(data)
    assert a.brief.expected_revenue == b.brief.expected_revenue
    assert a.kpis.reply_rate == b.kpis.reply_rate
    assert a.assistant.contacts[0].what_to_sell == b.assistant.contacts[0].what_to_sell
