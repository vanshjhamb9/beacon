"""Alembic migration: sales readiness engine append-only tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0031"
down_revision: str | Sequence[str] | None = "20260724_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "sales_readiness_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("eligible_for_revenue_hunter", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("visible_in_founder_queue", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="sre-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sales_readiness_snapshots_company_created", "sales_readiness_snapshots", ["company_id", "created_at"])
    op.create_index("ix_sales_readiness_snapshots_status", "sales_readiness_snapshots", ["status"])
    op.create_index("ix_sales_readiness_snapshots_rh", "sales_readiness_snapshots", ["eligible_for_revenue_hunter"])

    op.create_table(
        "sales_identity_scores",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("sales_readiness_snapshots.id"), nullable=True),
        sa.Column("identity_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("missing_fields", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sales_contact_readiness",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("sales_readiness_snapshots.id"), nullable=True),
        sa.Column("coverage_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("verified_email_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_phone_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sales_intent_scores",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("sales_readiness_snapshots.id"), nullable=True),
        sa.Column("level", sa.String(32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sales_service_matches_v2",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("sales_readiness_snapshots.id"), nullable=True),
        sa.Column("recommended_service", sa.String(255), nullable=False),
        sa.Column("estimated_value", sa.String(64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sales_revenue_potential",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("sales_readiness_snapshots.id"), nullable=True),
        sa.Column("deal_size", sa.String(32), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sales_cycle", sa.String(32), nullable=True),
        sa.Column("recommended_founder_time", sa.String(32), nullable=True),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sales_trust_scores",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("sales_readiness_snapshots.id"), nullable=True),
        sa.Column("overall", sa.Float(), nullable=False, server_default="0"),
        sa.Column("breakdown", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sales_trust_scores")
    op.drop_table("sales_revenue_potential")
    op.drop_table("sales_service_matches_v2")
    op.drop_table("sales_intent_scores")
    op.drop_table("sales_contact_readiness")
    op.drop_table("sales_identity_scores")
    op.drop_table("sales_readiness_snapshots")
