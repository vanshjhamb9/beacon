from time import perf_counter

from intelligence_improvement import ImprovementPipeline
from tests.intelligence_improvement.test_improvement_pipeline import make_feedback


def test_improvement_pipeline_processes_feedback_batch_quickly() -> None:
    feedback = make_feedback() * 250

    started = perf_counter()
    report = ImprovementPipeline().process(
        feedback=feedback,
        quality_rule_feedback=[],
        classifier_feedback=[],
        predictions=[],
    )
    elapsed_ms = (perf_counter() - started) * 1000.0

    assert report.overview["feedback_events"] == 500
    assert elapsed_ms < 500
