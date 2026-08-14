from pathlib import Path

from app.models.production_validation import LeadReadinessRow, ProductionAlertRow, ProductionValidationSnapshot


def test_production_validation_tablenames() -> None:
    assert ProductionValidationSnapshot.__tablename__ == "production_validation_snapshots"
    assert ProductionAlertRow.__tablename__ == "production_alerts"
    assert LeadReadinessRow.__tablename__ == "lead_readiness_scores"


def test_migration_0022_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260723_0022_create_production_validation_tables.py"
    text = migration.read_text(encoding="utf-8")
    assert "production_validation_snapshots" in text
    assert "production_alerts" in text
    assert "lead_readiness_scores" in text
    assert "20260723_0021" in text
