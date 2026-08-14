"""Create lead enrichment tables.

Revision ID: 20260719_0008
Revises: 20260710_0007
Create Date: 2026-07-19 01:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0008"
down_revision: str | None = "20260710_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "enrichment_reports",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("business_pain", sa.Text(), nullable=False),
        sa.Column("recommended_service", sa.String(255), nullable=False),
        sa.Column("buyer_persona", sa.String(128), nullable=False),
        sa.Column("estimated_budget", sa.String(128), nullable=True),
        sa.Column("priority", sa.String(32), nullable=True),
        sa.Column("why_now", sa.Text(), nullable=False),
        sa.Column("best_outreach_angle", sa.Text(), nullable=False),
        sa.Column("profile_completeness", sa.Float(), nullable=False),
        sa.Column("contact_availability", sa.Float(), nullable=False),
        sa.Column("technology_confidence", sa.Float(), nullable=False),
        sa.Column("decision_maker_confidence", sa.Float(), nullable=False),
        sa.Column("overall_enrichment_confidence", sa.Float(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("lead_profile", _json(), nullable=False),
        sa.Column("processing_latency_ms", sa.Float(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_enrichment_reports_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_enrichment_reports_opportunity_id_opportunities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enrichment_reports")),
    )
    op.create_index("ix_enrichment_reports_company_created", "enrichment_reports", ["company_id", "created_at"])
    op.create_index(
        "ix_enrichment_reports_opportunity_created", "enrichment_reports", ["opportunity_id", "created_at"]
    )

    op.create_table(
        "enriched_company_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("sub_industry", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("employee_count_estimate", sa.Integer(), nullable=True),
        sa.Column("company_size_range", sa.String(64), nullable=True),
        sa.Column("revenue_estimate", sa.String(128), nullable=True),
        sa.Column("field_attributions", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_enriched_company_profiles_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name=op.f("fk_enriched_company_profiles_opportunity_id_opportunities"),
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_enriched_company_profiles_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enriched_company_profiles")),
    )
    op.create_index(
        "ix_enriched_company_profiles_company_created", "enriched_company_profiles", ["company_id", "created_at"]
    )
    op.create_index("ix_enriched_company_profiles_opportunity", "enriched_company_profiles", ["opportunity_id"])

    op.create_table(
        "company_contacts",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("label", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_contacts_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_contacts_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_contacts")),
    )
    op.create_index("ix_company_contacts_company_kind", "company_contacts", ["company_id", "kind"])

    op.create_table(
        "company_people",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("linkedin_url", sa.String(1024), nullable=True),
        sa.Column("work_email", sa.String(320), nullable=True),
        sa.Column("business_phone", sa.String(64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_people_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_people_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_people")),
    )
    op.create_index("ix_company_people_company_role", "company_people", ["company_id", "role"])

    op.create_table(
        "company_social_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("handle", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_company_social_profiles_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_social_profiles_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_social_profiles")),
    )
    op.create_index(
        "ix_company_social_profiles_company_platform", "company_social_profiles", ["company_id", "platform"]
    )

    op.create_table(
        "company_technologies",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("signal", sa.String(255), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_company_technologies_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_technologies_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_technologies")),
    )
    op.create_index("ix_company_technologies_company_name", "company_technologies", ["company_id", "name"])

    op.create_table(
        "company_team_insights",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leadership_team_size", sa.Integer(), nullable=True),
        sa.Column("engineering_team_estimate", sa.Integer(), nullable=True),
        sa.Column("support_team_estimate", sa.Integer(), nullable=True),
        sa.Column("operations_team_estimate", sa.Integer(), nullable=True),
        sa.Column("recent_hires", _json(), nullable=False),
        sa.Column("open_positions", _json(), nullable=False),
        sa.Column("hiring_trends", sa.Text(), nullable=True),
        sa.Column("attributions", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_company_team_insights_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_team_insights_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_team_insights")),
    )
    op.create_index(
        "ix_company_team_insights_company_created", "company_team_insights", ["company_id", "created_at"]
    )

    op.create_table(
        "company_jobs",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_jobs_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_jobs_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_jobs")),
    )
    op.create_index("ix_company_jobs_company_title", "company_jobs", ["company_id", "title"])

    op.create_table(
        "company_enrichment_history",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_company_enrichment_history_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name=op.f("fk_company_enrichment_history_opportunity_id_opportunities"),
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_company_enrichment_history_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_enrichment_history")),
    )
    op.create_index(
        "ix_company_enrichment_history_company_created",
        "company_enrichment_history",
        ["company_id", "created_at"],
    )

    op.create_table(
        "enrichment_sources",
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("fields", _json(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("licensed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_enrichment_sources_enrichment_report_id_enrichment_reports"),
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_enrichment_sources_company_id_companies")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enrichment_sources")),
    )
    op.create_index(
        "ix_enrichment_sources_report_source", "enrichment_sources", ["enrichment_report_id", "source"]
    )


def downgrade() -> None:
    op.drop_index("ix_enrichment_sources_report_source", table_name="enrichment_sources")
    op.drop_table("enrichment_sources")
    op.drop_index("ix_company_enrichment_history_company_created", table_name="company_enrichment_history")
    op.drop_table("company_enrichment_history")
    op.drop_index("ix_company_jobs_company_title", table_name="company_jobs")
    op.drop_table("company_jobs")
    op.drop_index("ix_company_team_insights_company_created", table_name="company_team_insights")
    op.drop_table("company_team_insights")
    op.drop_index("ix_company_technologies_company_name", table_name="company_technologies")
    op.drop_table("company_technologies")
    op.drop_index("ix_company_social_profiles_company_platform", table_name="company_social_profiles")
    op.drop_table("company_social_profiles")
    op.drop_index("ix_company_people_company_role", table_name="company_people")
    op.drop_table("company_people")
    op.drop_index("ix_company_contacts_company_kind", table_name="company_contacts")
    op.drop_table("company_contacts")
    op.drop_index("ix_enriched_company_profiles_opportunity", table_name="enriched_company_profiles")
    op.drop_index("ix_enriched_company_profiles_company_created", table_name="enriched_company_profiles")
    op.drop_table("enriched_company_profiles")
    op.drop_index("ix_enrichment_reports_opportunity_created", table_name="enrichment_reports")
    op.drop_index("ix_enrichment_reports_company_created", table_name="enrichment_reports")
    op.drop_table("enrichment_reports")
