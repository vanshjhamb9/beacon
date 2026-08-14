"""Create data verification and coverage tables.

Revision ID: 20260719_0009
Revises: 20260719_0008
Create Date: 2026-07-19 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0009"
down_revision: str | None = "20260719_0008"
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
        "verification_reports",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("overall_data_quality", sa.Float(), nullable=False),
        sa.Column("overall_readiness", sa.Float(), nullable=False),
        sa.Column("coverage_percent", sa.Float(), nullable=False),
        sa.Column("verification_percent", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("freshness_status", sa.String(32), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(64), nullable=False),
        sa.Column("automatic_actions", _json(), nullable=False),
        sa.Column("reason_codes", _json(), nullable=False),
        sa.Column("missing_fields", _json(), nullable=False),
        sa.Column("readiness_checklist", _json(), nullable=False),
        sa.Column("explanation", _json(), nullable=False),
        sa.Column("result_payload", _json(), nullable=False),
        sa.Column("processing_latency_ms", sa.Float(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_verification_reports_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_verification_reports_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_verification_reports_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verification_reports")),
    )
    op.create_index("ix_verification_reports_company_created", "verification_reports", ["company_id", "created_at"])
    op.create_index("ix_verification_reports_enrichment", "verification_reports", ["enrichment_report_id"])

    op.create_table(
        "profile_completeness",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_completeness", sa.Float(), nullable=False),
        sa.Column("company_profile_completeness", sa.Float(), nullable=False),
        sa.Column("contact_completeness", sa.Float(), nullable=False),
        sa.Column("leadership_completeness", sa.Float(), nullable=False),
        sa.Column("technology_completeness", sa.Float(), nullable=False),
        sa.Column("revenue_completeness", sa.Float(), nullable=False),
        sa.Column("hiring_completeness", sa.Float(), nullable=False),
        sa.Column("social_profile_completeness", sa.Float(), nullable=False),
        sa.Column("evidence_completeness", sa.Float(), nullable=False),
        sa.Column("timeline_completeness", sa.Float(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_profile_completeness_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_profile_completeness_verification_report_id_verification_reports"),
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_profile_completeness_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profile_completeness")),
    )
    op.create_index("ix_profile_completeness_company_created", "profile_completeness", ["company_id", "created_at"])

    op.create_table(
        "field_verification",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("value", _json(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("freshness_status", sa.String(32), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False),
        sa.Column("confirmed_by", _json(), nullable=False),
        sa.Column("conflicting_sources", _json(), nullable=False),
        sa.Column("is_canonical", sa.Boolean(), nullable=False),
        sa.Column("conflict_explanation", sa.Text(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_field_verification_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_field_verification_verification_report_id_verification_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_field_verification")),
    )
    op.create_index("ix_field_verification_report_field", "field_verification", ["verification_report_id", "field_name"])

    op.create_table(
        "coverage_metrics",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("present_fields", sa.Integer(), nullable=False),
        sa.Column("expected_fields", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("missing_fields", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_coverage_metrics_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_coverage_metrics_verification_report_id_verification_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_coverage_metrics")),
    )
    op.create_index("ix_coverage_metrics_report_category", "coverage_metrics", ["verification_report_id", "category"])

    op.create_table(
        "freshness_metrics",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=True),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("freshness_status", sa.String(32), nullable=False),
        sa.Column("scope", sa.String(32), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_freshness_metrics_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_freshness_metrics_verification_report_id_verification_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_freshness_metrics")),
    )
    op.create_index("ix_freshness_metrics_report_created", "freshness_metrics", ["verification_report_id", "created_at"])

    op.create_table(
        "trust_scores",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_trust_scores_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_trust_scores_verification_report_id_verification_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trust_scores")),
    )
    op.create_index("ix_trust_scores_report_scope", "trust_scores", ["verification_report_id", "scope"])

    op.create_table(
        "verification_history",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_verification_history_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_verification_history_verification_report_id_verification_reports"),
        ),
        sa.ForeignKeyConstraint(
            ["enrichment_report_id"],
            ["enrichment_reports.id"],
            name=op.f("fk_verification_history_enrichment_report_id_enrichment_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verification_history")),
    )
    op.create_index("ix_verification_history_company_created", "verification_history", ["company_id", "created_at"])

    op.create_table(
        "connector_statistics",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("average_latency_ms", sa.Float(), nullable=False),
        sa.Column("failure_rate", sa.Float(), nullable=False),
        sa.Column("coverage", sa.Float(), nullable=False),
        sa.Column("fields_returned", sa.Integer(), nullable=False),
        sa.Column("average_confidence", sa.Float(), nullable=False),
        sa.Column("companies_enriched", sa.Integer(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_connector_statistics_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_connector_statistics_verification_report_id_verification_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_connector_statistics")),
    )
    op.create_index(
        "ix_connector_statistics_report_connector", "connector_statistics", ["verification_report_id", "connector"]
    )

    op.create_table(
        "field_statistics",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("present", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_field_statistics_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["verification_report_id"],
            ["verification_reports.id"],
            name=op.f("fk_field_statistics_verification_report_id_verification_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_field_statistics")),
    )
    op.create_index("ix_field_statistics_report_field", "field_statistics", ["verification_report_id", "field_name"])


def downgrade() -> None:
    op.drop_index("ix_field_statistics_report_field", table_name="field_statistics")
    op.drop_table("field_statistics")
    op.drop_index("ix_connector_statistics_report_connector", table_name="connector_statistics")
    op.drop_table("connector_statistics")
    op.drop_index("ix_verification_history_company_created", table_name="verification_history")
    op.drop_table("verification_history")
    op.drop_index("ix_trust_scores_report_scope", table_name="trust_scores")
    op.drop_table("trust_scores")
    op.drop_index("ix_freshness_metrics_report_created", table_name="freshness_metrics")
    op.drop_table("freshness_metrics")
    op.drop_index("ix_coverage_metrics_report_category", table_name="coverage_metrics")
    op.drop_table("coverage_metrics")
    op.drop_index("ix_field_verification_report_field", table_name="field_verification")
    op.drop_table("field_verification")
    op.drop_index("ix_profile_completeness_company_created", table_name="profile_completeness")
    op.drop_table("profile_completeness")
    op.drop_index("ix_verification_reports_enrichment", table_name="verification_reports")
    op.drop_index("ix_verification_reports_company_created", table_name="verification_reports")
    op.drop_table("verification_reports")
