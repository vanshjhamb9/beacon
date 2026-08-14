from time import perf_counter

from opportunity_engine import OpportunityPipeline
from tests.opportunity_engine.test_opportunity_pipeline import make_input


def test_opportunity_pipeline_processes_batch_quickly() -> None:
    pipeline = OpportunityPipeline()
    inputs = [make_input() for _ in range(50)]

    started = perf_counter()
    decisions = [pipeline.process(item) for item in inputs]
    elapsed_ms = (perf_counter() - started) * 1000

    assert len(decisions) == 50
    assert elapsed_ms < 750
