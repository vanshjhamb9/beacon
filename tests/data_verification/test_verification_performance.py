from time import perf_counter

from data_verification import VerificationPipeline
from tests.data_verification.test_verification_pipeline import make_input


def test_verification_pipeline_processes_batch_quickly() -> None:
    pipeline = VerificationPipeline()
    inputs = [make_input() for _ in range(50)]

    started = perf_counter()
    results = [pipeline.process(item) for item in inputs]
    elapsed_ms = (perf_counter() - started) * 1000

    assert len(results) == 50
    assert elapsed_ms < 1500
    assert all(0 <= result.overall_data_quality <= 100 for result in results)
