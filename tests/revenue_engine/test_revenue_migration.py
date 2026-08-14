from pathlib import Path

from app.models.revenue import (
    DealEstimate,
    RecommendationHistory,
    RevenueBuyerPersona,
    SalesPlaybook,
    ServiceCatalog,
    ServiceRule,
    SolutionMatch,
)


def test_revenue_orm_tables_match_mvp_contract() -> None:
    assert ServiceCatalog.__tablename__ == "services"
    assert ServiceRule.__tablename__ == "service_rules"
    assert SolutionMatch.__tablename__ == "solution_matches"
    assert RevenueBuyerPersona.__tablename__ == "buyer_personas"
    assert DealEstimate.__tablename__ == "deal_estimates"
    assert SalesPlaybook.__tablename__ == "sales_playbooks"
    assert RecommendationHistory.__tablename__ == "recommendation_history"


def test_migration_0007_defines_required_tables_and_seed() -> None:
    migration = Path("apps/api/alembic/versions/20260710_0007_create_revenue_tables.py").read_text(
        encoding="utf-8"
    )
    for table in [
        "services",
        "solution_matches",
        "buyer_personas",
        "deal_estimates",
        "service_rules",
        "sales_playbooks",
        "recommendation_history",
    ]:
        assert f'"{table}"' in migration
    assert 'revision: str = "20260710_0007"' in migration
    assert 'down_revision: str | None = "20260710_0006"' in migration
    assert "COMAI" in migration
    assert "Custom AI Development" in migration
    assert "Shopify Development" in migration
    assert "_seed_services" in migration
    assert "_seed_service_rules" in migration


def test_deal_estimate_and_playbook_columns_are_present() -> None:
    estimate_columns = set(DealEstimate.__table__.columns.keys())
    playbook_columns = set(SalesPlaybook.__table__.columns.keys())
    assert {
        "project_size",
        "implementation_complexity",
        "estimated_budget_range",
        "priority_level",
    }.issubset(estimate_columns)
    assert {
        "business_pain",
        "recommended_service",
        "why",
        "conversation_angle",
        "decision_maker",
        "expected_outcome",
        "risk",
    }.issubset(playbook_columns)
