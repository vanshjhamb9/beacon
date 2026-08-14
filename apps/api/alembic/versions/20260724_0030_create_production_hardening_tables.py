"""Alembic migration: production hardening append-only tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0030"
down_revision: str | Sequence[str] | None = "20260724_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "ph_admission_decisions",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("reasons", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ph_admission_decisions_verdict_created", "ph_admission_decisions", ["verdict", "created_at"])
    op.create_index("ix_ph_admission_decisions_company", "ph_admission_decisions", ["company_id"])

    op.create_table(
        "ph_contact_readiness",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("lead_quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("founder_queue_visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("details", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ph_contact_readiness_company_created", "ph_contact_readiness", ["company_id", "created_at"])
    op.create_index("ix_ph_contact_readiness_status", "ph_contact_readiness", ["status"])

    op.create_table(
        "ph_company_merges",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("canonical_company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("merged_company_id", _uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("match_keys", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ph_company_merges_canonical", "ph_company_merges", ["canonical_company_id"])

    op.create_table(
        "ph_trust_snapshots",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("metrics", _json(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", _json(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="ph1-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ph_trust_snapshots")
    op.drop_table("ph_company_merges")
    op.drop_table("ph_contact_readiness")
    op.drop_table("ph_admission_decisions")
