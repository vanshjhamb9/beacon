"""Alembic migration: revenue data recovery (RDI v1) append-only tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0032"
down_revision: str | Sequence[str] | None = "20260724_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "rdi_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("recovery_stage", sa.String(64), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("identity_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("website_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_fake", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("eligible_for_revenue_hunter", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("visible_in_founder_queue", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="rdi-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rdi_snapshots_company_created", "rdi_snapshots", ["company_id", "created_at"])
    op.create_index("ix_rdi_snapshots_stage", "rdi_snapshots", ["recovery_stage"])
    op.create_index("ix_rdi_snapshots_rh", "rdi_snapshots", ["eligible_for_revenue_hunter"])
    op.create_index("ix_rdi_snapshots_sales_ready", "rdi_snapshots", ["status"])

    op.create_table(
        "rdi_recovery_queue",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("rdi_snapshots.id"), nullable=True),
        sa.Column("company_name", sa.String(512), nullable=False, server_default="UNKNOWN"),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("priority", sa.Float(), nullable=False, server_default="0"),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("next_action", sa.String(512), nullable=False, server_default="UNKNOWN"),
        sa.Column("blocked_reasons", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rdi_recovery_queue_stage_priority", "rdi_recovery_queue", ["stage", "priority"])
    op.create_index("ix_rdi_recovery_queue_company", "rdi_recovery_queue", ["company_id"])

    op.create_table(
        "rdi_dossiers",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("rdi_snapshots.id"), nullable=True),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_deal", sa.String(64), nullable=True),
        sa.Column("primary_service", sa.String(255), nullable=True),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rdi_dossiers_company_created", "rdi_dossiers", ["company_id", "created_at"])

    op.create_table(
        "rdi_metrics_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("identity_complete", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("website_verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fake_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("founder_queue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recovery_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("duplicate_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="rdi-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rdi_metrics_created", "rdi_metrics_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_table("rdi_metrics_snapshots")
    op.drop_table("rdi_dossiers")
    op.drop_table("rdi_recovery_queue")
    op.drop_table("rdi_snapshots")
