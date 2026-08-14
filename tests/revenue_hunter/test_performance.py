import time
from uuid import uuid4

from revenue_hunter import RevenueHunterPipeline, RevenueHunterInput


def test_pipeline_throughput_budget() -> None:
    pipeline = RevenueHunterPipeline()
    started = time.perf_counter()
    for idx in range(100):
        pipeline.process(
            RevenueHunterInput(
                company_id=uuid4(),
                company_name=f"Co {idx}",
                industry="SaaS",
                country="USA",
                employee_count=120,
                technologies=["crm", "zendesk"],
                signals=["funding", "hiring", "automation"],
                pains=["manual workflows", "growing support"],
                hiring_roles=["Support Engineer"],
                hiring_count=3,
                decision_makers=[{"name": "A", "role": "CTO"}],
                opportunity_score=70,
            )
        )
    assert (time.perf_counter() - started) < 2.5
