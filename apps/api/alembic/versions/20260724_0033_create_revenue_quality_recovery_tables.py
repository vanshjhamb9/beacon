"""Alembic migration: revenue quality recovery (RQP v1) append-only tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0033"
down_revision: str | Sequence[str] | None = "20260724_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "rqp_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("surface_admitted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("surface_status", sa.String(64), nullable=True),
        sa.Column("identity_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sales_ready_badge", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="rqp-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rqp_snapshots_company_created", "rqp_snapshots", ["company_id", "created_at"])
    op.create_index("ix_rqp_snapshots_verdict", "rqp_snapshots", ["verdict"])
    op.create_index("ix_rqp_snapshots_surface", "rqp_snapshots", ["surface_admitted"])

    op.create_table(
        "rqp_daily_kpis",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("collected_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recovered_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("identity_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("website_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("contacts_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("decision_makers_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sales_ready_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("enterprise_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fake_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="rqp-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rqp_daily_kpis_created", "rqp_daily_kpis", ["created_at"])

    op.create_table(
        "rqp_acceptance_gates",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("production_unlocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failures", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="rqp-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rqp_acceptance_created", "rqp_acceptance_gates", ["created_at"])

    op.create_table(
        "rqp_golden_dataset",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", sa.String(64), nullable=False),
        sa.Column("company_name", sa.String(512), nullable=False),
        sa.Column("website", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("linkedin_company", sa.String(512), nullable=False),
        sa.Column("industry", sa.String(128), nullable=False),
        sa.Column("country", sa.String(64), nullable=False),
        sa.Column("employee_estimate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("benchmark_version", sa.String(64), nullable=False, server_default="beacon-gold-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rqp_golden_company", "rqp_golden_dataset", ["company_id"])


def downgrade() -> None:
    op.drop_table("rqp_golden_dataset")
    op.drop_table("rqp_acceptance_gates")
    op.drop_table("rqp_daily_kpis")
    op.drop_table("rqp_snapshots")
