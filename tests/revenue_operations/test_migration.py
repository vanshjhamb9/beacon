from pathlib import Path

from app.models.revenue_operations import (
    AgencyStatisticRow,
    LearningRecommendationRow,
    RevenueAlertRow,
    RevenueForecastRow,
    RevenueMemoryRow,
    RevenueMetricRow,
    RevenueOperationSnapshot,
    RevenueReplayRow,
)


def test_roc_tablenames() -> None:
    assert RevenueOperationSnapshot.__tablename__ == "revenue_operation_snapshots"
    assert RevenueAlertRow.__tablename__ == "revenue_alerts"
    assert RevenueForecastRow.__tablename__ == "revenue_forecasts"
    assert RevenueMemoryRow.__tablename__ == "revenue_memory"
    assert RevenueReplayRow.__tablename__ == "revenue_replays"
    assert RevenueMetricRow.__tablename__ == "revenue_operation_metrics"
    assert LearningRecommendationRow.__tablename__ == "revenue_operation_learning"
    assert AgencyStatisticRow.__tablename__ == "agency_statistics"


def test_migration_0024_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260724_0024_create_revenue_operations_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in [
        "revenue_operation_snapshots",
        "revenue_alerts",
        "revenue_forecasts",
        "revenue_memory",
        "revenue_replays",
        "revenue_operation_metrics",
        "revenue_operation_learning",
        "agency_statistics",
    ]:
        assert table in text
    assert "20260723_0023" in text
    assert 'revision: str = "20260724_0024"' in text
    # Avoid colliding with existing revenue_metrics table from Revenue Engine
    assert 'op.create_table(\n        "revenue_metrics"' not in text


def test_alert_and_memory_immutable_contracts() -> None:
    assert "dedupe_key" in RevenueAlertRow.__table__.columns.keys()
    assert "lifecycle" in RevenueAlertRow.__table__.columns.keys()
    assert "immutable" in RevenueMemoryRow.__table__.columns.keys()
    assert "modifies_production" in LearningRecommendationRow.__table__.columns.keys()
