from pathlib import Path

from app.models.founder_os import (
    FounderAnalyticsEventRow,
    FounderDailyBriefRow,
    FounderRevenueTaskRow,
    FounderTimelineEventRow,
)


def test_founder_os_models_tablename_contract() -> None:
    assert FounderDailyBriefRow.__tablename__ == "founder_daily_briefs"
    assert FounderRevenueTaskRow.__tablename__ == "founder_revenue_tasks"
    assert FounderTimelineEventRow.__tablename__ == "founder_timeline_events"
    assert FounderAnalyticsEventRow.__tablename__ == "founder_analytics_events"


def test_migration_0018_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260723_0018_create_founder_os_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "founder_daily_briefs",
        "founder_revenue_tasks",
        "founder_timeline_events",
        "founder_analytics_events",
    ):
        assert table in text
    assert "20260723_0017" in text
