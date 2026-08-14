from datetime import UTC, datetime
from uuid import uuid4

from intelligence_improvement.evaluation.engine import EvaluationEngine
from intelligence_improvement.models import FeedbackSignal, FeedbackSource, ImprovementArea, RulePerformanceMetric
from intelligence_improvement.optimization.engine import OptimizationEngine


def test_evaluation_engine_ranks_collectors_by_conversion() -> None:
    signals = [
        FeedbackSignal(
            source=FeedbackSource.HUMAN_REVIEW,
            area=ImprovementArea.COLLECTOR,
            entity_key="reddit",
            entity_id=uuid4(),
            outcome="accepted",
            score=80.0,
            occurred_at=datetime.now(UTC),
        ),
        FeedbackSignal(
            source=FeedbackSource.HUMAN_REVIEW,
            area=ImprovementArea.COLLECTOR,
            entity_key="rss",
            entity_id=uuid4(),
            outcome="rejected",
            score=20.0,
            occurred_at=datetime.now(UTC),
        ),
    ]

    metrics = EvaluationEngine().collector_performance(signals)

    assert metrics[0].entity_key == "reddit"
    assert metrics[0].precision == 100.0


def test_optimization_recommends_human_approved_rule_adjustment() -> None:
    recommendations = OptimizationEngine().rule_recommendations(
        [
            RulePerformanceMetric(
                rule_key="hiring.signal",
                rule_type="classifier",
                times_fired=5,
                correct_decisions=1,
                incorrect_decisions=4,
                override_rate=20.0,
                confidence=20.0,
            )
        ]
    )

    assert recommendations
    assert recommendations[0].requires_approval is True
    assert "Reduce rule weight" in recommendations[0].recommendation
