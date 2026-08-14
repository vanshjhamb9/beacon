"""Create decision maker discovery tables.

Revision ID: 20260719_0011
Revises: 20260719_0010
Create Date: 2026-07-19 03:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0011"
down_revision: str | None = "20260719_0010"
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
        "decision_discovery_reports",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verification_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("business_pain", sa.Text(), nullable=False),
        sa.Column("recommended_service", sa.String(255), nullable=False),
        sa.Column("primary_decision_maker_name", sa.String(255), nullable=True),
        sa.Column("primary_decision_maker_role", sa.String(128), nullable=True),
        sa.Column("secondary_decision_maker_name", sa.String(255), nullable=True),
        sa.Column("secondary_decision_maker_role", sa.String(128), nullable=True),
        sa.Column("buyer_match_confidence", sa.Float(), nullable=False),
        sa.Column("overall_discovery_score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("no_public_contact_message", sa.Text(), nullable=True),
        sa.Column("best_outreach_sequence", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("source_attribution", _json(), nullable=False),
        sa.Column("report_payload", _json(), nullable=False),
        sa.Column("processing_latency_ms", sa.Float(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_decision_discovery_reports_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_decision_discovery_reports_opportunity_id_opportunities")),
        sa.ForeignKeyConstraint(["enrichment_report_id"], ["enrichment_reports.id"], name=op.f("fk_decision_discovery_reports_enrichment_report_id_enrichment_reports")),
        sa.ForeignKeyConstraint(["verification_report_id"], ["verification_reports.id"], name=op.f("fk_decision_discovery_reports_verification_report_id_verification_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_discovery_reports")),
    )
    op.create_index("ix_decision_discovery_reports_company_created", "decision_discovery_reports", ["company_id", "created_at"])
    op.create_index("ix_decision_discovery_reports_opportunity_created", "decision_discovery_reports", ["opportunity_id", "created_at"])

    op.create_table(
        "decision_makers",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("normalized_role", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("seniority_rank", sa.Integer(), nullable=False),
        sa.Column("work_email", sa.String(255), nullable=True),
        sa.Column("business_phone", sa.String(64), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("is_secondary", sa.Boolean(), nullable=False),
        sa.Column("buyer_match_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_decision_makers_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_decision_makers_discovery_report_id_decision_discovery_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_makers")),
    )
    op.create_index("ix_decision_makers_report_role", "decision_makers", ["discovery_report_id", "role"])
    op.create_index("ix_decision_makers_company_role", "decision_makers", ["company_id", "role"])

    op.create_table(
        "company_departments",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("signal_strength", sa.Float(), nullable=False),
        sa.Column("headcount_signal", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_departments_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_company_departments_discovery_report_id_decision_discovery_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_departments")),
    )
    op.create_index("ix_company_departments_report_name", "company_departments", ["discovery_report_id", "name"])

    op.create_table(
        "company_contact_channels",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("is_verified_public", sa.Boolean(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_contact_channels_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_company_contact_channels_discovery_report_id_decision_discovery_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_contact_channels")),
    )
    op.create_index("ix_company_contact_channels_report_rank", "company_contact_channels", ["discovery_report_id", "rank"])
    op.create_index("ix_company_contact_channels_company_kind", "company_contact_channels", ["company_id", "kind"])

    op.create_table(
        "company_public_profiles",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("handle", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_public_profiles_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_company_public_profiles_discovery_report_id_decision_discovery_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_public_profiles")),
    )
    op.create_index("ix_company_public_profiles_report_platform", "company_public_profiles", ["discovery_report_id", "platform"])

    op.create_table(
        "company_leadership",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_leadership_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_company_leadership_discovery_report_id_decision_discovery_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_leadership")),
    )
    op.create_index("ix_company_leadership_report_title", "company_leadership", ["discovery_report_id", "title"])

    op.create_table(
        "decision_confidence",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leadership_confidence", sa.Float(), nullable=False),
        sa.Column("department_confidence", sa.Float(), nullable=False),
        sa.Column("contact_confidence", sa.Float(), nullable=False),
        sa.Column("buyer_match_confidence", sa.Float(), nullable=False),
        sa.Column("overall_discovery_score", sa.Float(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_decision_confidence_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_decision_confidence_discovery_report_id_decision_discovery_reports")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_confidence")),
    )
    op.create_index("ix_decision_confidence_report", "decision_confidence", ["discovery_report_id"])

    op.create_table(
        "decision_history",
        sa.Column("discovery_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", _json(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_decision_history_company_id_companies")),
        sa.ForeignKeyConstraint(["discovery_report_id"], ["decision_discovery_reports.id"], name=op.f("fk_decision_history_discovery_report_id_decision_discovery_reports")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_decision_history_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_history")),
    )
    op.create_index("ix_decision_history_company_created", "decision_history", ["company_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_decision_history_company_created", table_name="decision_history")
    op.drop_table("decision_history")
    op.drop_index("ix_decision_confidence_report", table_name="decision_confidence")
    op.drop_table("decision_confidence")
    op.drop_index("ix_company_leadership_report_title", table_name="company_leadership")
    op.drop_table("company_leadership")
    op.drop_index("ix_company_public_profiles_report_platform", table_name="company_public_profiles")
    op.drop_table("company_public_profiles")
    op.drop_index("ix_company_contact_channels_company_kind", table_name="company_contact_channels")
    op.drop_index("ix_company_contact_channels_report_rank", table_name="company_contact_channels")
    op.drop_table("company_contact_channels")
    op.drop_index("ix_company_departments_report_name", table_name="company_departments")
    op.drop_table("company_departments")
    op.drop_index("ix_decision_makers_company_role", table_name="decision_makers")
    op.drop_index("ix_decision_makers_report_role", table_name="decision_makers")
    op.drop_table("decision_makers")
    op.drop_index("ix_decision_discovery_reports_opportunity_created", table_name="decision_discovery_reports")
    op.drop_index("ix_decision_discovery_reports_company_created", table_name="decision_discovery_reports")
    op.drop_table("decision_discovery_reports")
