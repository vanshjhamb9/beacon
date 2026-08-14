from pathlib import Path

from app.models.client_execution import (
    ClientHandoffRow,
    ClientHealthSnapshot,
    ClientMemoryRow,
    ClientProfile,
    ClientProject,
    DeliverySnapshot,
    RenewalPredictionRow,
    UpsellRecommendationRow,
)


def test_aep_tablenames() -> None:
    assert ClientProfile.__tablename__ == "client_profiles"
    assert ClientProject.__tablename__ == "client_projects"
    assert ClientHealthSnapshot.__tablename__ == "client_health_snapshots"
    assert ClientMemoryRow.__tablename__ == "client_memory"
    assert ClientHandoffRow.__tablename__ == "client_handoffs"
    assert UpsellRecommendationRow.__tablename__ == "upsell_recommendations"
    assert RenewalPredictionRow.__tablename__ == "renewal_predictions"
    assert DeliverySnapshot.__tablename__ == "delivery_snapshots"


def test_migration_0026_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260724_0026_create_client_execution_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in [
        "client_profiles",
        "client_projects",
        "client_health_snapshots",
        "client_memory",
        "client_handoffs",
        "upsell_recommendations",
        "renewal_predictions",
        "delivery_snapshots",
    ]:
        assert table in text
    assert "20260724_0025" in text
    assert 'revision: str = "20260724_0026"' in text


def test_memory_immutable_and_upsell_approval_flags() -> None:
    assert "immutable" in ClientMemoryRow.__table__.columns.keys()
    assert "requires_founder_approval" in UpsellRecommendationRow.__table__.columns.keys()
    assert "modifies_production" in UpsellRecommendationRow.__table__.columns.keys()
