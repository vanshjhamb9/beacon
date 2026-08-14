from uuid import uuid4

from revenue_operations.analytics.replay import RevenueReplayEngine
from revenue_operations.forecasting.engine import RevenueForecastEngine
from revenue_operations.memory.engine import AgencyMemoryEngine
from revenue_operations.models.types import OpportunitySignal, RevenueOperationsInput


def test_replay_lost_path() -> None:
    replay = RevenueReplayEngine().replay_opportunity(
        OpportunitySignal(company_name="Lost", lost=True, why_lost="No budget", reply_waiting=True)
    )
    assert replay.outcome == "lost"
    assert any(e.stage == "lost" for e in replay.events)


def test_replay_batch_matches_opportunities() -> None:
    item = RevenueOperationsInput(
        opportunities=[
            OpportunitySignal(company_name="A", opportunity_id=uuid4()),
            OpportunitySignal(company_name="B", opportunity_id=uuid4(), won=True),
        ]
    )
    replays = RevenueReplayEngine().build(item)
    assert len(replays) == 2
    assert {r.company_name for r in replays} == {"A", "B"}


def test_forecast_risk_when_below_target() -> None:
    pack = RevenueForecastEngine().forecast(
        RevenueOperationsInput(
            opportunities=[OpportunitySignal(company_name="Small", probability=10, pipeline_value=1000)],
            revenue_target_week=50000,
        )
    )
    assert any("below weekly target" in r.lower() for r in pack.risk_analysis)


def test_memory_search_empty_query_returns_all() -> None:
    eng = AgencyMemoryEngine()
    records = eng.build(
        RevenueOperationsInput(
            opportunities=[OpportunitySignal(company_name="Mem", industry="Retail", service="CRM", meeting_today=True)]
        )
    )
    assert eng.search(records, "") == records
    assert eng.search(records, "retail")
