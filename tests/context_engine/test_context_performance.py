from time import perf_counter

from context_engine import ContextPipeline
from tests.context_engine.test_context_pipeline import make_input


def test_context_pipeline_processes_batch_quickly() -> None:
    pipeline = ContextPipeline()
    items = [make_input("automation") for _ in range(50)]

    started = perf_counter()
    results = [pipeline.process(item) for item in items]
    elapsed_ms = (perf_counter() - started) * 1000

    assert len(results) == 50
    assert elapsed_ms < 500
