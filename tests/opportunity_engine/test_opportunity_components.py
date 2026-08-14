from datetime import UTC, datetime, timedelta
from uuid import uuid4

from opportunity_engine.decay.policies import DecayPolicyCatalog
from opportunity_engine.lifecycle.engine import LifecycleEngine
from opportunity_engine.models import OpportunityEvidenceItem, OpportunityStatus
from opportunity_engine.recommendations.engine import RecommendationEngine


def test_decay_weights_recent_evidence_more_than_old_evidence() -> None:
    catalog = DecayPolicyCatalog()
    now = datetime.now(UTC)
    recent = OpportunityEvidenceItem(
        source_type="signal",
        reference_id=uuid4(),
        category="funding",
        summary="recent",
        confidence=80.0,
        occurred_at=now - timedelta(days=2),
    )
    old = recent.model_copy(update={"reference_id": uuid4(), "occurred_at": now - timedelta(days=180)})

    assert catalog.weight(recent, now=now) > catalog.weight(old, now=now)


def test_lifecycle_transitions_are_score_driven() -> None:
    engine = LifecycleEngine()

    assert (
        engine.determine(opportunity_score=86.0, confidence_score=80.0, urgency_score=75.0)
        == OpportunityStatus.HIGH_INTENT
    )
    assert (
        engine.determine(opportunity_score=45.0, confidence_score=55.0, urgency_score=35.0)
        == OpportunityStatus.WATCHING
    )


def test_recommendation_engine_escalates_conflicts_to_more_evidence() -> None:
    recommendation = RecommendationEngine().recommend(
        status=OpportunityStatus.HIGH_INTENT,
        opportunity_score=90.0,
        urgency_score=90.0,
        confidence_score=85.0,
        conflict_penalty=20.0,
    )

    assert recommendation.action.value == "collect_more_evidence"
    assert "Conflicting evidence" in recommendation.reasons[0]
