from pathlib import Path

from app.models.target_account import (
    HunterJobRow,
    ICPProfileRow,
    TAIImprovementRecommendation,
    TargetAccount,
)


def test_target_account_models_tablename_contract() -> None:
    assert ICPProfileRow.__tablename__ == "icp_profiles"
    assert TargetAccount.__tablename__ == "target_accounts"
    assert HunterJobRow.__tablename__ == "hunter_jobs"
    assert TAIImprovementRecommendation.__tablename__ == "tai_improvement_recommendations"


def test_migration_0016_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260720_0016_create_target_account_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "icp_profiles",
        "target_accounts",
        "hunter_jobs",
        "tai_improvement_recommendations",
    ):
        assert table in text
    assert "20260720_0015" in text
