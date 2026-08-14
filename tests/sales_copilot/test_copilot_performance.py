import time
from uuid import uuid4

from sales_copilot import SalesCopilotPipeline
from tests.sales_copilot.test_copilot_pipeline import make_input


def test_copilot_pipeline_latency_budget() -> None:
    pipeline = SalesCopilotPipeline()
    started = time.perf_counter()
    for _ in range(20):
        pipeline.process(make_input(company_id=uuid4(), opportunity_id=uuid4()), version=1)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 3000.0
