from pathlib import Path

from app.models.account_intelligence import (
    AIPBuyingCommitteeRow,
    AIPTechnologyProfileRow,
    AccountProfileRow,
    RelationshipGraphEdgeRow,
    RelationshipGraphNodeRow,
    VerifiedContactRow,
    WebsiteProfileV2Row,
)


def test_aip_tablenames() -> None:
    assert AccountProfileRow.__tablename__ == "aip_account_profiles"
    assert AIPBuyingCommitteeRow.__tablename__ == "aip_buying_committee"
    assert VerifiedContactRow.__tablename__ == "aip_verified_contacts"
    assert AIPTechnologyProfileRow.__tablename__ == "technology_profiles_aip"
    assert WebsiteProfileV2Row.__tablename__ == "website_profiles_v2"
    assert RelationshipGraphNodeRow.__tablename__ == "aip_relationship_graph_nodes"
    assert RelationshipGraphEdgeRow.__tablename__ == "aip_relationship_graph_edges"


def test_migration_0028_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260724_0028_create_account_intelligence_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in [
        "aip_account_profiles",
        "aip_company_locations",
        "aip_company_departments",
        "aip_buying_committee",
        "aip_verified_contacts",
        "aip_contact_verification",
        "technology_profiles_aip",
        "website_profiles_v2",
        "aip_financial_profiles",
        "aip_business_profiles",
        "aip_growth_profiles",
        "ai_readiness_reports",
        "sales_readiness_reports",
        "aip_relationship_graph_nodes",
        "aip_relationship_graph_edges",
        "aip_confidence_reports",
        "aip_verification_history",
        "aip_field_sources",
        "aip_industry_benchmarks",
    ]:
        assert table in text
    assert "20260724_0027" in text
    assert 'revision: str = "20260724_0028"' in text


def test_immutable_graph_and_no_fabricate_flag() -> None:
    assert "immutable" in RelationshipGraphNodeRow.__table__.columns.keys()
    assert "fabricated" in AIPBuyingCommitteeRow.__table__.columns.keys()
