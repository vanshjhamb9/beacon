from pathlib import Path

from app.models.verification import (
    ConnectorStatisticRow,
    CoverageMetric,
    FieldStatistic,
    FieldVerification,
    FreshnessMetric,
    ProfileCompleteness,
    TrustScore,
    VerificationHistory,
    VerificationReport,
)


def test_verification_orm_tables_match_contract() -> None:
    assert VerificationReport.__tablename__ == "verification_reports"
    assert ProfileCompleteness.__tablename__ == "profile_completeness"
    assert FieldVerification.__tablename__ == "field_verification"
    assert CoverageMetric.__tablename__ == "coverage_metrics"
    assert FreshnessMetric.__tablename__ == "freshness_metrics"
    assert TrustScore.__tablename__ == "trust_scores"
    assert VerificationHistory.__tablename__ == "verification_history"
    assert ConnectorStatisticRow.__tablename__ == "connector_statistics"
    assert FieldStatistic.__tablename__ == "field_statistics"


def test_migration_0009_defines_required_tables() -> None:
    migration = Path("apps/api/alembic/versions/20260719_0009_create_data_verification_tables.py").read_text(
        encoding="utf-8"
    )
    for table in [
        "profile_completeness",
        "verification_reports",
        "field_verification",
        "coverage_metrics",
        "freshness_metrics",
        "trust_scores",
        "verification_history",
        "connector_statistics",
        "field_statistics",
    ]:
        assert f'"{table}"' in migration
    assert 'revision: str = "20260719_0009"' in migration
    assert 'down_revision: str | None = "20260719_0008"' in migration
