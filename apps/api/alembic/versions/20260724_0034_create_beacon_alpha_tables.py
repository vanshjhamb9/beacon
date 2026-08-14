"""Alembic migration: Beacon Alpha revenue dataset perfection tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0034"
down_revision: str | Sequence[str] | None = "20260724_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "alpha_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("score_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("founder_visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("best_service", sa.String(255), nullable=True),
        sa.Column("primary_bucket", sa.String(64), nullable=True),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alpha_snapshots_company_created", "alpha_snapshots", ["company_id", "created_at"])
    op.create_index("ix_alpha_snapshots_verdict", "alpha_snapshots", ["verdict"])
    op.create_index("ix_alpha_snapshots_score", "alpha_snapshots", ["score_total"])

    op.create_table(
        "alpha_qa_decisions",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("rating", sa.String(64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewer", sa.String(128), nullable=True),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alpha_qa_company", "alpha_qa_decisions", ["company_id"])
    op.create_index("ix_alpha_qa_rating", "alpha_qa_decisions", ["rating"])

    op.create_table(
        "alpha_acceptance_gates",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("live_outreach_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failures", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alpha_acceptance_created", "alpha_acceptance_gates", ["created_at"])

    op.create_table(
        "alpha_founder_queue",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="alpha-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alpha_fq_score", "alpha_founder_queue", ["score"])


def downgrade() -> None:
    op.drop_table("alpha_founder_queue")
    op.drop_table("alpha_acceptance_gates")
    op.drop_table("alpha_qa_decisions")
    op.drop_table("alpha_snapshots")
