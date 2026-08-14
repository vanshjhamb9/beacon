from outcome_intelligence.evaluation.engine import OutcomeEvaluationEngine
from outcome_intelligence.learning.engine import OutcomeLearningEngine
from outcome_intelligence.metrics.lifecycle import normalize_stage, outcome_score, stage_order
from outcome_intelligence.models.types import OutcomeLifecycle, RateMetrics


def test_lifecycle_order_and_scores() -> None:
    stages = stage_order()
    assert stages[0] is OutcomeLifecycle.NEW
    assert stages[-3] is OutcomeLifecycle.WON
    assert outcome_score("won") == 100.0
    assert outcome_score("lost") == 0.0
    assert normalize_stage("Meeting Scheduled") is OutcomeLifecycle.MEETING_SCHEDULED
    assert normalize_stage("closed_won") is OutcomeLifecycle.WON


def test_opportunity_score_accuracy() -> None:
    engine = OutcomeEvaluationEngine()
    metrics = engine.opportunity_score_accuracy(
        [
            {"opportunity_score": 90.0, "lifecycle_stage": "won"},
            {"opportunity_score": 20.0, "lifecycle_stage": "lost"},
            {"opportunity_score": 70.0, "lifecycle_stage": "proposal_sent"},
        ]
    )
    assert len(metrics) == 1
    assert metrics[0].sample_size == 3
    assert metrics[0].accuracy_score > 0


def test_revenue_recommendation_accuracy() -> None:
    engine = OutcomeEvaluationEngine()
    metrics = engine.revenue_recommendation_accuracy(
        [
            {"recommended_service": "AI Automation", "lifecycle_stage": "won"},
            {"recommended_service": "AI Automation", "lifecycle_stage": "lost"},
            {"recommended_service": "ERP", "lifecycle_stage": "proposal_sent"},
        ]
    )
    assert metrics[0].category == "revenue_recommendation"
    assert metrics[0].sample_size == 3


def test_learning_recommendations_require_approval() -> None:
    engine = OutcomeLearningEngine()
    rates = RateMetrics(
        meeting_rate=10.0,
        reply_rate=8.0,
        proposal_rate=5.0,
        close_rate=2.0,
        contacted_count=20,
        replied_count=2,
        meeting_count=4,
        proposal_count=1,
        won_count=0,
        lost_count=5,
        total_opportunities=20,
    )
    recs = engine.recommendations(
        rates=rates,
        collector_accuracy=[],
        service_accuracy=[],
        industry_accuracy=[],
        persona_accuracy=[],
        prediction_accuracy=[],
        revenue_by_service=[],
    )
    assert recs
    assert all(item.requires_approval for item in recs)
