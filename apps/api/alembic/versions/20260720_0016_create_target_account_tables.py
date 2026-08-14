"""Create target account intelligence tables.

Revision ID: 20260720_0016
Revises: 20260720_0015
Create Date: 2026-07-20 04:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0016"
down_revision: str | None = "20260720_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base() -> list[sa.Column[object]]:
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
        "icp_profiles",
        *_base(),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("service_match", sa.String(128), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("company_size_min", sa.Integer(), nullable=True),
        sa.Column("company_size_max", sa.Integer(), nullable=True),
        sa.Column("employee_count_min", sa.Integer(), nullable=True),
        sa.Column("employee_count_max", sa.Integer(), nullable=True),
        sa.Column("industries", _json(), nullable=False),
        sa.Column("revenue_bands", _json(), nullable=False),
        sa.Column("countries", _json(), nullable=False),
        sa.Column("funding_stages", _json(), nullable=False),
        sa.Column("hiring_signals", _json(), nullable=False),
        sa.Column("technology_stack", _json(), nullable=False),
        sa.Column("business_models", _json(), nullable=False),
        sa.Column("growth_signals", _json(), nullable=False),
        sa.Column("decision_makers", _json(), nullable=False),
        sa.Column("pain_points", _json(), nullable=False),
        sa.Column("buying_signals", _json(), nullable=False),
        sa.Column("negative_signals", _json(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_icp_profiles")),
        sa.UniqueConstraint("key", name=op.f("uq_icp_profiles_key")),
    )
    op.create_index("ix_icp_profiles_priority_active", "icp_profiles", ["priority", "is_active"])

    op.create_table(
        "target_accounts",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("icp_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("matched_icp_key", sa.String(128), nullable=True),
        sa.Column("matched_icp_name", sa.String(255), nullable=True),
        sa.Column("service_match", sa.String(128), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("fit_score", sa.Float(), nullable=False),
        sa.Column("intent_score", sa.Float(), nullable=False),
        sa.Column("budget_score", sa.Float(), nullable=False),
        sa.Column("budget_band", sa.String(32), nullable=True),
        sa.Column("urgency_score", sa.Float(), nullable=False),
        sa.Column("accessibility_score", sa.Float(), nullable=False),
        sa.Column("competition_score", sa.Float(), nullable=False),
        sa.Column("revenue_opportunity_score", sa.Float(), nullable=False),
        sa.Column("tier", sa.String(32), nullable=False),
        sa.Column("why_now", sa.Text(), nullable=False),
        sa.Column("buying_signals", _json(), nullable=False),
        sa.Column("negative_signals", _json(), nullable=False),
        sa.Column("score_breakdown", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("explanations", _json(), nullable=False),
        sa.Column("hunter_triggered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hunter_tasks", _json(), nullable=False),
        sa.Column("proceed_to_copilot", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("scoring_version", sa.String(64), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_target_accounts_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_target_accounts_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["icp_profile_id"], ["icp_profiles.id"], name=op.f("fk_target_accounts_icp_profile_id_icp_profiles")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_target_accounts")),
    )
    op.create_index("ix_target_accounts_score", "target_accounts", ["revenue_opportunity_score"])
    op.create_index("ix_target_accounts_tier_score", "target_accounts", ["tier", "revenue_opportunity_score"])
    op.create_index("ix_target_accounts_company", "target_accounts", ["company_id"])

    op.create_table(
        "hunter_jobs",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("tasks", _json(), nullable=False),
        sa.Column("completed_tasks", _json(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_hunter_jobs_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["target_account_id"],
            ["target_accounts.id"],
            name=op.f("fk_hunter_jobs_target_account_id_target_accounts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hunter_jobs")),
    )
    op.create_index("ix_hunter_jobs_status", "hunter_jobs", ["status", "created_at"])

    op.create_table(
        "tai_improvement_recommendations",
        *_base(),
        sa.Column("target_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(64), nullable=False),
        sa.Column("area", sa.String(64), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Float(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(32), nullable=False, server_default="proposed"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["target_account_id"],
            ["target_accounts.id"],
            name=op.f("fk_tai_improvement_recommendations_target_account_id_target_accounts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tai_improvement_recommendations")),
    )


def downgrade() -> None:
    op.drop_table("tai_improvement_recommendations")
    op.drop_index("ix_hunter_jobs_status", table_name="hunter_jobs")
    op.drop_table("hunter_jobs")
    op.drop_index("ix_target_accounts_company", table_name="target_accounts")
    op.drop_index("ix_target_accounts_tier_score", table_name="target_accounts")
    op.drop_index("ix_target_accounts_score", table_name="target_accounts")
    op.drop_table("target_accounts")
    op.drop_index("ix_icp_profiles_priority_active", table_name="icp_profiles")
    op.drop_table("icp_profiles")
