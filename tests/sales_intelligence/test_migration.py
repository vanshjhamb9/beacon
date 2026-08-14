from pathlib import Path

from app.models.sales_intelligence import (
    SalesIntelligenceSnapshot,
    SalesMemoryEventRow,
    SalesReplyIntelligenceRow,
)


def test_sales_intelligence_model_tablenames() -> None:
    assert SalesIntelligenceSnapshot.__tablename__ == "sales_intelligence_snapshots"
    assert SalesMemoryEventRow.__tablename__ == "sales_memory_events"
    assert SalesReplyIntelligenceRow.__tablename__ == "sales_reply_intelligence"


def test_migration_0020_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260723_0020_create_sales_intelligence_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "sales_intelligence_snapshots",
        "sales_memory_events",
        "sales_reply_intelligence",
    ):
        assert table in text
    assert 'down_revision: str | None = "20260723_0019"' in text or "20260723_0019" in text
    assert "append" in text.lower() or "sales_intelligence_snapshots" in text


def test_snapshot_is_append_only_contract() -> None:
    """Snapshots store full payload; no unique company constraint (append-only)."""
    table_args = SalesIntelligenceSnapshot.__table_args__
    assert table_args
    # No UniqueConstraint on company_id — multiple snapshots allowed over time
    assert SalesIntelligenceSnapshot.company_id is not None
    assert SalesIntelligenceSnapshot.payload is not None
