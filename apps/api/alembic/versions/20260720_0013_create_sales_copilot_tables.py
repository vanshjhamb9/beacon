"""Create AI sales copilot tables.

Revision ID: 20260720_0013
Revises: 20260719_0012
Create Date: 2026-07-20 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0013"
down_revision: str | None = "20260719_0012"
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
        "sales_prompt_versions",
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_prompt_template", sa.Text(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("model_hint", sa.String(128), nullable=False),
        sa.Column("provider_hint", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_prompt_versions")),
        sa.UniqueConstraint("version", name=op.f("uq_sales_prompt_versions_version")),
    )
    op.create_index("ix_sales_prompt_versions_active", "sales_prompt_versions", ["is_active", "created_at"])

    op.create_table(
        "sales_templates",
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("style", sa.String(64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", _json(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_templates")),
    )
    op.create_index("ix_sales_templates_kind_style", "sales_templates", ["kind", "style"])

    op.create_table(
        "sales_packages",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("recommended_service", sa.String(255), nullable=False),
        sa.Column("business_pain", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("review_status", sa.String(32), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("llm_provider", sa.String(64), nullable=False),
        sa.Column("llm_model", sa.String(128), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("generation_time_ms", sa.Float(), nullable=False),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=False),
        sa.Column("quality_scores", _json(), nullable=False),
        sa.Column("sections", _json(), nullable=False),
        sa.Column("style_variants", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("package_payload", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_sales_packages_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_packages_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_packages")),
    )
    op.create_index("ix_sales_packages_company_created", "sales_packages", ["company_id", "created_at"])
    op.create_index("ix_sales_packages_opportunity_version", "sales_packages", ["opportunity_id", "version"])
    op.create_index("ix_sales_packages_review_status", "sales_packages", ["review_status", "created_at"])

    op.create_table(
        "sales_drafts",
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("style", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("subject_lines", _json(), nullable=False),
        sa.Column("attribution", _json(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["package_id"], ["sales_packages.id"], name=op.f("fk_sales_drafts_package_id_sales_packages")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_sales_drafts_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_drafts_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_drafts")),
    )
    op.create_index("ix_sales_drafts_package_kind_style", "sales_drafts", ["package_id", "kind", "style"])

    op.create_table(
        "sales_generation_logs",
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("llm_provider", sa.String(64), nullable=False),
        sa.Column("llm_model", sa.String(128), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("generation_time_ms", sa.Float(), nullable=False),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_payload", _json(), nullable=False),
        sa.Column("response_payload", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["package_id"], ["sales_packages.id"], name=op.f("fk_sales_generation_logs_package_id_sales_packages")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_sales_generation_logs_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_generation_logs_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_generation_logs")),
    )
    op.create_index("ix_sales_generation_logs_company_created", "sales_generation_logs", ["company_id", "created_at"])

    op.create_table(
        "sales_feedback",
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["package_id"], ["sales_packages.id"], name=op.f("fk_sales_feedback_package_id_sales_packages")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_sales_feedback_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_feedback_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_feedback")),
    )
    op.create_index("ix_sales_feedback_package_created", "sales_feedback", ["package_id", "created_at"])

    op.create_table(
        "sales_versions",
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", _json(), nullable=False),
        sa.Column("change_reason", sa.String(255), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["package_id"], ["sales_packages.id"], name=op.f("fk_sales_versions_package_id_sales_packages")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_sales_versions_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_versions_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_versions")),
        sa.UniqueConstraint("opportunity_id", "version", name=op.f("uq_sales_versions_opportunity_id_version")),
    )
    op.create_index("ix_sales_versions_company_version", "sales_versions", ["company_id", "version"])


def downgrade() -> None:
    op.drop_index("ix_sales_versions_company_version", table_name="sales_versions")
    op.drop_table("sales_versions")
    op.drop_index("ix_sales_feedback_package_created", table_name="sales_feedback")
    op.drop_table("sales_feedback")
    op.drop_index("ix_sales_generation_logs_company_created", table_name="sales_generation_logs")
    op.drop_table("sales_generation_logs")
    op.drop_index("ix_sales_drafts_package_kind_style", table_name="sales_drafts")
    op.drop_table("sales_drafts")
    op.drop_index("ix_sales_packages_review_status", table_name="sales_packages")
    op.drop_index("ix_sales_packages_opportunity_version", table_name="sales_packages")
    op.drop_index("ix_sales_packages_company_created", table_name="sales_packages")
    op.drop_table("sales_packages")
    op.drop_index("ix_sales_templates_kind_style", table_name="sales_templates")
    op.drop_table("sales_templates")
    op.drop_index("ix_sales_prompt_versions_active", table_name="sales_prompt_versions")
    op.drop_table("sales_prompt_versions")
