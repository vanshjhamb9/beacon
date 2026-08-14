"""Alembic migration: Ground Truth Recovery (Alpha+) tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0035"
down_revision: str | Sequence[str] | None = "20260724_0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "gt_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("trust", sa.Float(), nullable=False, server_default="0"),
        sa.Column("readiness", sa.Float(), nullable=False, server_default="0"),
        sa.Column("lock_unlocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("questions_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-plus-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gt_snapshots_company_created", "gt_snapshots", ["company_id", "created_at"])
    op.create_index("ix_gt_snapshots_verdict", "gt_snapshots", ["verdict"])

    op.create_table(
        "gt_daily_reports",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("report_date", sa.String(32), nullable=False),
        sa.Column("collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_quality", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-plus-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gt_daily_reports_date", "gt_daily_reports", ["report_date"])

    op.create_table(
        "gt_acceptance_gates",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("production_unlocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failures", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-plus-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gt_acceptance_created", "gt_acceptance_gates", ["created_at"])

    op.create_table(
        "gt_founder_queue",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trust", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-plus-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gt_fq_rank", "gt_founder_queue", ["rank"])


def downgrade() -> None:
    op.drop_table("gt_founder_queue")
    op.drop_table("gt_acceptance_gates")
    op.drop_table("gt_daily_reports")
    op.drop_table("gt_snapshots")
