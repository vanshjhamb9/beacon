from pathlib import Path

from app.models.enrichment import (
    CompanyContact,
    CompanyEnrichmentHistory,
    CompanyJob,
    CompanyPerson,
    CompanySocialProfile,
    CompanyTeamInsight,
    CompanyTechnology,
    EnrichedCompanyProfile,
    EnrichmentReport,
    EnrichmentSource,
)


def test_enrichment_orm_tables_match_contract() -> None:
    assert EnrichmentReport.__tablename__ == "enrichment_reports"
    assert EnrichedCompanyProfile.__tablename__ == "enriched_company_profiles"
    assert CompanyContact.__tablename__ == "company_contacts"
    assert CompanyPerson.__tablename__ == "company_people"
    assert CompanySocialProfile.__tablename__ == "company_social_profiles"
    assert CompanyTechnology.__tablename__ == "company_technologies"
    assert CompanyTeamInsight.__tablename__ == "company_team_insights"
    assert CompanyJob.__tablename__ == "company_jobs"
    assert CompanyEnrichmentHistory.__tablename__ == "company_enrichment_history"
    assert EnrichmentSource.__tablename__ == "enrichment_sources"


def test_migration_0008_defines_required_tables() -> None:
    migration = Path("apps/api/alembic/versions/20260719_0008_create_lead_enrichment_tables.py").read_text(
        encoding="utf-8"
    )
    for table in [
        "enrichment_reports",
        "enriched_company_profiles",
        "company_contacts",
        "company_people",
        "company_social_profiles",
        "company_technologies",
        "company_team_insights",
        "company_jobs",
        "company_enrichment_history",
        "enrichment_sources",
    ]:
        assert f'"{table}"' in migration
    assert 'revision: str = "20260719_0008"' in migration
    assert 'down_revision: str | None = "20260710_0007"' in migration


def test_enrichment_report_columns_cover_sales_ready_contract() -> None:
    columns = set(EnrichmentReport.__table__.columns.keys())
    assert {
        "company_id",
        "opportunity_id",
        "business_pain",
        "recommended_service",
        "buyer_persona",
        "why_now",
        "best_outreach_angle",
        "overall_enrichment_confidence",
        "lead_profile",
        "evidence_chain",
    }.issubset(columns)
