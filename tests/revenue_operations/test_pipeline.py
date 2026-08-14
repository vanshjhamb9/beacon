from uuid import uuid4

from revenue_operations import RevenueOperationsPipeline
from revenue_operations.models.types import OpportunitySignal, RevenueOperationsInput


def _batch(n: int) -> RevenueOperationsInput:
    opps = [
        OpportunitySignal(
            opportunity_id=uuid4(),
            company_id=uuid4(),
            company_name=f"Co {i}",
            industry="SaaS" if i % 2 == 0 else "Healthcare",
            service="AI Automation",
            probability=40 + (i % 50),
            pipeline_value=10000 + i * 100,
            days_in_stage=i % 14,
            reply_waiting=i % 5 == 0,
            meeting_today=i % 7 == 0,
            proposal_pending=i % 9 == 0,
            at_risk=i % 11 == 0,
            radar_hints=["funding"] if i % 4 == 0 else ["hiring software developers"],
            decision_makers=["CEO"],
            technologies=["Python"],
        )
        for i in range(n)
    ]
    return RevenueOperationsInput(opportunities=opps, campaigns_running=5, revenue_closed=50000)


def test_pipeline_deterministic() -> None:
    item = _batch(5)
    a = RevenueOperationsPipeline().process(item)
    b = RevenueOperationsPipeline().process(item)
    assert a.control_tower.pipeline_value == b.control_tower.pipeline_value
    assert a.forecast.this_week.amount == b.forecast.this_week.amount
    assert a.command_center.revenue_score == b.command_center.revenue_score
    assert len(a.alerts) == len(b.alerts)


def test_pipeline_scales_to_many_opportunities() -> None:
    d = RevenueOperationsPipeline().process(_batch(50))
    assert len(d.replays) == 50
    assert d.control_tower.pipeline_value > 0
    assert d.operational_metrics.discovery_rate == 100


def test_pipeline_evidence_backed() -> None:
    d = RevenueOperationsPipeline().process(_batch(3))
    assert any(e.startswith("scoring_version:") for e in d.evidence_chain)
    assert d.control_tower.evidence
    assert d.forecast.evidence
    assert d.learning.evidence
