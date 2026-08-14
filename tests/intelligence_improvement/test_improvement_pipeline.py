from datetime import UTC, datetime
from uuid import uuid4

from intelligence_improvement import FeedbackSignal, FeedbackSource, ImprovementArea, ImprovementPipeline
from intelligence_improvement.models import PredictionEvaluation


def make_feedback() -> list[FeedbackSignal]:
    now = datetime.now(UTC)
    return [
        FeedbackSignal(
            source=FeedbackSource.HUMAN_REVIEW,
            area=ImprovementArea.COLLECTOR,
            entity_key="reddit",
            entity_id=uuid4(),
            outcome="accepted",
            score=85.0,
            occurred_at=now,
            details={"latency_ms": 20.0},
        ),
        FeedbackSignal(
            source=FeedbackSource.HUMAN_REVIEW,
            area=ImprovementArea.COLLECTOR,
            entity_key="rss",
            entity_id=uuid4(),
            outcome="rejected",
            score=35.0,
            occurred_at=now,
            details={"latency_ms": 12.0},
        ),
    ]


def test_improvement_pipeline_generates_report_and_recommendations() -> None:
    feedback = make_feedback()
    rule_feedback = [
        FeedbackSignal(
            source=FeedbackSource.HUMAN_REVIEW,
            area=ImprovementArea.QUALITY_RULE,
            entity_key="spam.high_probability",
            entity_id=uuid4(),
            outcome="incorrect",
            score=30.0,
            occurred_at=datetime.now(UTC),
        )
        for _ in range(3)
    ]
    predictions = [
        PredictionEvaluation(
            opportunity_id=uuid4(),
            predicted_score=90.0,
            actual_outcome_score=0.0,
            prediction_error=90.0,
            outcome_label="lost",
        )
    ]

    report = ImprovementPipeline().process(
        feedback=feedback,
        quality_rule_feedback=rule_feedback,
        classifier_feedback=[],
        predictions=predictions,
    )

    assert report.overview["feedback_events"] == 5
    assert report.collector_rankings
    assert report.rule_rankings[0].rule_key == "spam.high_probability"
    assert report.opportunity_accuracy["average_prediction_error"] == 90.0
    assert report.recommendations
