import time
from uuid import uuid4

from decision_discovery import DecisionDiscoveryPipeline
from tests.decision_discovery.test_discovery_pipeline import make_input


def test_discovery_pipeline_latency_budget() -> None:
    pipeline = DecisionDiscoveryPipeline()
    started = time.perf_counter()
    for _ in range(25):
        pipeline.process(make_input(company_id=uuid4(), opportunity_id=uuid4()))
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 1500.0
