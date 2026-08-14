from pathlib import Path

from app.models.live_revenue import (
    LiveRevenueLifecycleEvent,
    LiveRevenueProposalVersion,
    LiveRevenueRun,
    LiveRevenueTrackingEvent,
)


def test_lre_model_tablenames() -> None:
    assert LiveRevenueRun.__tablename__ == "live_revenue_runs"
    assert LiveRevenueLifecycleEvent.__tablename__ == "live_revenue_lifecycle_events"
    assert LiveRevenueTrackingEvent.__tablename__ == "live_revenue_tracking_events"
    assert LiveRevenueProposalVersion.__tablename__ == "live_revenue_proposal_versions"


def test_migration_0021_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260723_0021_create_live_revenue_execution_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "live_revenue_runs",
        "live_revenue_lifecycle_events",
        "live_revenue_tracking_events",
        "live_revenue_proposal_versions",
    ):
        assert table in text
    assert "20260723_0020" in text
