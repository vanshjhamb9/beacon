from datetime import UTC, datetime
from uuid import uuid4

from revenue_optimization import (
    SCORING_VERSION,
    RevenueOptimizationPipeline,
    RevenueOptimizationService,
)
from revenue_optimization.models.types import OutreachEvent, ROIPInput


def _event(**overrides: object) -> OutreachEvent:
    payload: dict[str, object] = {
        "event_id": f"evt-{uuid4()}",
        "company_id": uuid4(),
        "company_name": "Acme SaaS",
        "campaign_id": "camp-1",
        "industry": "SaaS",
        "company_size_band": "50-200",
        "channel": "email",
        "subject": "Quick idea for Acme",
        "cta": "book_meeting",
        "offer": "AI Automation",
        "delivered": True,
        "opened": True,
        "open_count": 2,
        "open_hour": 9,
        "open_weekday": 1,
        "open_device": "desktop",
        "open_country": "US",
        "calendly_clicks": 1,
        "website_visits": 2,
        "replied": True,
        "reply_hours": 12.0,
        "reply_text": "interested let's meet",
        "meeting_booked": True,
        "proposal_sent": True,
        "closed_won": True,
        "deal_value": 25000.0,
        "followup_number": 2,
        "sequence_length": 4,
        "delay_days": 4.0,
        "timezone": "UTC",
        "founder_actor": True,
        "evidence": ["unit:true"],
    }
    payload.update(overrides)
    return OutreachEvent.model_validate(payload)


def _input(n: int = 5, **event_overrides: object) -> ROIPInput:
    events = [_event(company_name=f"Co{i}", event_id=f"e{i}", **event_overrides) for i in range(n)]
    return ROIPInput(
        events=events,
        previous_period_events=events[: max(1, n // 2)],
        portfolio_assets=[
            {
                "asset_id": "cs-1",
                "asset_type": "case_study",
                "title": "SaaS automation win",
                "industry": "SaaS",
                "company_size": "50-200",
            }
        ],
        now=datetime.now(UTC),
    )


def test_scoring_version() -> None:
    assert SCORING_VERSION == "roip-v1"


def test_pipeline_deterministic() -> None:
    data = _input(8)
    a = RevenueOptimizationPipeline().process(data)
    b = RevenueOptimizationPipeline().process(data)
    assert a.email_metrics.open_rate == b.email_metrics.open_rate
    assert a.founder.revenue == b.founder.revenue
    assert [r.recommendation_id for r in a.recommendations] == [r.recommendation_id for r in b.recommendations]
    assert a.learning.modifies_production is False


def test_pipeline_evidence_and_guardrails() -> None:
    d = RevenueOptimizationPipeline().process(_input())
    assert "compose_only:true" in d.evidence_chain
    assert "no_gpt:true" in d.evidence_chain
    assert "never_auto_apply:true" in d.evidence_chain
    assert all(r.requires_founder_approval for r in d.recommendations)
    assert all(r.modifies_production is False for r in d.recommendations)


def test_service_evaluate_many() -> None:
    out = RevenueOptimizationService().evaluate_many([_input(2), _input(3)])
    assert len(out) == 2


def test_search_filters() -> None:
    decision = RevenueOptimizationService().evaluate(_input(6, industry="Healthcare", offer="AI Audit"))
    found = RevenueOptimizationService().search(decision, query="health", filters={"industry": "Healthcare"})
    assert found["industries"]
