from pathlib import Path

from app.models.decision import (
    CompanyContactChannel,
    CompanyDepartment,
    CompanyLeadership,
    CompanyPublicProfile,
    DecisionConfidence,
    DecisionDiscoveryReport,
    DecisionHistory,
    DecisionMaker,
)


def test_decision_models_tablename_contract() -> None:
    assert DecisionDiscoveryReport.__tablename__ == "decision_discovery_reports"
    assert DecisionMaker.__tablename__ == "decision_makers"
    assert CompanyDepartment.__tablename__ == "company_departments"
    assert CompanyContactChannel.__tablename__ == "company_contact_channels"
    assert CompanyPublicProfile.__tablename__ == "company_public_profiles"
    assert CompanyLeadership.__tablename__ == "company_leadership"
    assert DecisionConfidence.__tablename__ == "decision_confidence"
    assert DecisionHistory.__tablename__ == "decision_history"


def test_migration_0011_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260719_0011_create_decision_discovery_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "decision_makers",
        "company_departments",
        "company_contact_channels",
        "company_public_profiles",
        "company_leadership",
        "decision_discovery_reports",
        "decision_confidence",
        "decision_history",
    ):
        assert table in text
    assert 'revision: str = "20260719_0011"' in text
    assert 'down_revision: str | None = "20260719_0010"' in text
