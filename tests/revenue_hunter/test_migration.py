from pathlib import Path

from app.models.revenue_hunter import (
    RevenueHunterDailyBrief,
    RevenueHunterDossier,
    RevenueHunterWorkQueueItem,
)


def test_revenue_hunter_models_tablename_contract() -> None:
    assert RevenueHunterDossier.__tablename__ == "revenue_hunter_dossiers"
    assert RevenueHunterWorkQueueItem.__tablename__ == "revenue_hunter_work_queue"
    assert RevenueHunterDailyBrief.__tablename__ == "revenue_hunter_daily_briefs"


def test_migration_0017_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260723_0017_create_revenue_hunter_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "revenue_hunter_dossiers",
        "revenue_hunter_work_queue",
        "revenue_hunter_daily_briefs",
    ):
        assert table in text
    assert "20260720_0016" in text
