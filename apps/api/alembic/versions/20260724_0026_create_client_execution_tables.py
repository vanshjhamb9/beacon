"""Create client execution / AEP tables.

Revision ID: 20260724_0026
Revises: 20260724_0025
Create Date: 2026-07-24 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0026"
down_revision: str | None = "20260724_0025"
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
        "client_profiles",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("contract_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("health_status", sa.String(32), nullable=False, server_default="healthy"),
        sa.Column("overall_health", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="aep-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_client_profiles_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_profiles")),
    )
    op.create_index("ix_aep_profiles_company_created", "client_profiles", ["company_id", "created_at"])
    op.create_index("ix_aep_profiles_stage", "client_profiles", ["stage"])

    op.create_table(
        "client_projects",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(64), nullable=True),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("at_risk", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_client_projects_company_id_companies")),
        sa.ForeignKeyConstraint(["profile_id"], ["client_profiles.id"], name=op.f("fk_client_projects_profile_id_client_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_projects")),
    )
    op.create_index("ix_aep_projects_company_created", "client_projects", ["company_id", "created_at"])

    op.create_table(
        "client_health_snapshots",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("overall_health", sa.Float(), nullable=False, server_default="0"),
        sa.Column("renewal_probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("upsell_probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_client_health_snapshots_company_id_companies")),
        sa.ForeignKeyConstraint(["profile_id"], ["client_profiles.id"], name=op.f("fk_client_health_snapshots_profile_id_client_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_health_snapshots")),
    )
    op.create_index("ix_aep_health_company_created", "client_health_snapshots", ["company_id", "created_at"])

    op.create_table(
        "client_memory",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("record_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", _json(), nullable=False),
        sa.Column("searchable_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_client_memory_company_id_companies")),
        sa.ForeignKeyConstraint(["profile_id"], ["client_profiles.id"], name=op.f("fk_client_memory_profile_id_client_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_memory")),
    )
    op.create_index("ix_aep_memory_company_created", "client_memory", ["company_id", "created_at"])
    op.create_index("ix_aep_memory_type", "client_memory", ["record_type"])

    op.create_table(
        "client_handoffs",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_client_handoffs_company_id_companies")),
        sa.ForeignKeyConstraint(["profile_id"], ["client_profiles.id"], name=op.f("fk_client_handoffs_profile_id_client_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_handoffs")),
    )
    op.create_index("ix_aep_handoffs_company_created", "client_handoffs", ["company_id", "created_at"])

    op.create_table(
        "upsell_recommendations",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_id", sa.String(64), nullable=False),
        sa.Column("service", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("requires_founder_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("modifies_production", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_approval"),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_upsell_recommendations_company_id_companies")),
        sa.ForeignKeyConstraint(["profile_id"], ["client_profiles.id"], name=op.f("fk_upsell_recommendations_profile_id_client_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_upsell_recommendations")),
    )
    op.create_index("ix_aep_upsells_company_created", "upsell_recommendations", ["company_id", "created_at"])
    op.create_index("ix_aep_upsells_rec_id", "upsell_recommendations", ["recommendation_id"])

    op.create_table(
        "renewal_predictions",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("renewal_date", sa.String(64), nullable=True),
        sa.Column("probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_renewal_predictions_company_id_companies")),
        sa.ForeignKeyConstraint(["profile_id"], ["client_profiles.id"], name=op.f("fk_renewal_predictions_profile_id_client_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_renewal_predictions")),
    )
    op.create_index("ix_aep_renewals_company_created", "renewal_predictions", ["company_id", "created_at"])

    op.create_table(
        "delivery_snapshots",
        *_base(),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("founder_view", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="aep-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_snapshots")),
    )
    op.create_index("ix_aep_delivery_created", "delivery_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_aep_delivery_created", table_name="delivery_snapshots")
    op.drop_table("delivery_snapshots")
    op.drop_index("ix_aep_renewals_company_created", table_name="renewal_predictions")
    op.drop_table("renewal_predictions")
    op.drop_index("ix_aep_upsells_rec_id", table_name="upsell_recommendations")
    op.drop_index("ix_aep_upsells_company_created", table_name="upsell_recommendations")
    op.drop_table("upsell_recommendations")
    op.drop_index("ix_aep_handoffs_company_created", table_name="client_handoffs")
    op.drop_table("client_handoffs")
    op.drop_index("ix_aep_memory_type", table_name="client_memory")
    op.drop_index("ix_aep_memory_company_created", table_name="client_memory")
    op.drop_table("client_memory")
    op.drop_index("ix_aep_health_company_created", table_name="client_health_snapshots")
    op.drop_table("client_health_snapshots")
    op.drop_index("ix_aep_projects_company_created", table_name="client_projects")
    op.drop_table("client_projects")
    op.drop_index("ix_aep_profiles_stage", table_name="client_profiles")
    op.drop_index("ix_aep_profiles_company_created", table_name="client_profiles")
    op.drop_table("client_profiles")
