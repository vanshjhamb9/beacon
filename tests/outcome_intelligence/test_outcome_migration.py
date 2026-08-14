from pathlib import Path

from app.models.outcomes import (
    CollectorAccuracy,
    ContactAttempt,
    CustomerFeedback,
    Deal,
    IndustryAccuracy,
    LearningMetric,
    Meeting,
    OpportunityOutcome,
    PersonaAccuracy,
    PredictionAccuracy,
    Proposal,
    ServiceAccuracy,
)


def test_outcome_models_tablename_contract() -> None:
    assert OpportunityOutcome.__tablename__ == "opportunity_outcomes"
    assert ContactAttempt.__tablename__ == "contact_attempts"
    assert Meeting.__tablename__ == "meetings"
    assert Proposal.__tablename__ == "proposals"
    assert Deal.__tablename__ == "deals"
    assert CustomerFeedback.__tablename__ == "customer_feedback"
    assert PredictionAccuracy.__tablename__ == "prediction_accuracy"
    assert ServiceAccuracy.__tablename__ == "service_accuracy"
    assert CollectorAccuracy.__tablename__ == "collector_accuracy"
    assert PersonaAccuracy.__tablename__ == "persona_accuracy"
    assert IndustryAccuracy.__tablename__ == "industry_accuracy"
    assert LearningMetric.__tablename__ == "learning_metrics"


def test_migration_0012_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260719_0012_create_outcome_intelligence_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "opportunity_outcomes",
        "contact_attempts",
        "meetings",
        "proposals",
        "deals",
        "customer_feedback",
        "prediction_accuracy",
        "service_accuracy",
        "collector_accuracy",
        "persona_accuracy",
        "industry_accuracy",
        "learning_metrics",
    ):
        assert table in text
    assert 'revision: str = "20260719_0012"' in text
    assert 'down_revision: str | None = "20260719_0011"' in text
