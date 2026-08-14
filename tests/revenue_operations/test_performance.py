import time
from uuid import uuid4

from revenue_operations import RevenueOperationsPipeline
from revenue_operations.models.types import OpportunitySignal, RevenueOperationsInput


def test_200_opportunity_evals_under_5_seconds() -> None:
    pipeline = RevenueOperationsPipeline()
    started = time.perf_counter()
    for i in range(200):
        pipeline.process(
            RevenueOperationsInput(
                opportunities=[
                    OpportunitySignal(
                        opportunity_id=uuid4(),
                        company_id=uuid4(),
                        company_name=f"Perf {i}",
                        industry="SaaS",
                        service="CRM",
                        probability=50 + (i % 40),
                        pipeline_value=20000 + i,
                        days_in_stage=i % 10,
                        reply_waiting=i % 6 == 0,
                        radar_hints=["ai adoption"] if i % 3 == 0 else [],
                        decision_makers=["VP"],
                    )
                ],
                campaigns_running=2,
            )
        )
    assert (time.perf_counter() - started) < 5.0


def test_dashboard_pack_under_1_second() -> None:
    opps = [
        OpportunitySignal(
            opportunity_id=uuid4(),
            company_name=f"Dash {i}",
            probability=60,
            pipeline_value=30000,
            meeting_today=i < 3,
            reply_waiting=i < 5,
            proposal_pending=i < 2,
            radar_hints=["funding", "hiring"],
            decision_makers=["CEO"],
            technologies=["Python", "AWS"],
        )
        for i in range(40)
    ]
    pipeline = RevenueOperationsPipeline()
    started = time.perf_counter()
    decision = pipeline.process(RevenueOperationsInput(opportunities=opps, campaigns_running=8, revenue_closed=120000))
    elapsed = time.perf_counter() - started
    assert elapsed < 1.0
    assert decision.command_center.greeting
    assert decision.control_tower.pipeline_value > 0
