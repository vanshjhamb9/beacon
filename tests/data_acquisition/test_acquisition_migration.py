from pathlib import Path

from app.models.acquisition import (
    AcquisitionDailyReport,
    CollectorRun,
    ConnectorAlertRecord,
    ConnectorBenchmarkSnapshot,
)


def test_acquisition_tables_exist() -> None:
    assert CollectorRun.__tablename__ == "collector_runs"
    assert ConnectorAlertRecord.__tablename__ == "connector_alerts"
    assert AcquisitionDailyReport.__tablename__ == "acquisition_daily_reports"
    assert ConnectorBenchmarkSnapshot.__tablename__ == "connector_benchmark_snapshots"


def test_migration_0010_defines_tables() -> None:
    migration = Path("apps/api/alembic/versions/20260719_0010_create_data_acquisition_tables.py").read_text(
        encoding="utf-8"
    )
    for table in [
        "collector_runs",
        "connector_alerts",
        "acquisition_daily_reports",
        "connector_benchmark_snapshots",
    ]:
        assert f'"{table}"' in migration
    assert 'revision: str = "20260719_0010"' in migration
    assert 'down_revision: str | None = "20260719_0009"' in migration
