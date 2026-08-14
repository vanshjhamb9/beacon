"""Create company resolution (CRE v1) tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0036"
down_revision = "20260724_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cre_snapshots",
        sa.Column("signal_id", sa.String(length=128), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_events.id"), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("company_domain", sa.String(length=255), nullable=True),
        sa.Column("identity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("website_valid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("admitted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rejection_explanation", sa.Text(), nullable=True),
        sa.Column("attribution_url", sa.String(length=1024), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(length=32), nullable=False, server_default="cre-v1"),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cre_snapshots_signal_id", "cre_snapshots", ["signal_id"])
    op.create_index("ix_cre_snapshots_source", "cre_snapshots", ["source"])
    op.create_index("ix_cre_snapshots_verdict", "cre_snapshots", ["verdict"])
    op.create_index("ix_cre_snapshots_company_domain", "cre_snapshots", ["company_domain"])

    op.create_table(
        "cre_admission_decisions",
        sa.Column("signal_id", sa.String(length=128), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_events.id"), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("admitted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(length=32), nullable=False, server_default="cre-v1"),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_cre_admission_decisions_signal_id", "cre_admission_decisions", ["signal_id"])

    op.create_table(
        "cre_rebuild_reports",
        sa.Column("total_raw_signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolution_success_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rejection_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("identity_confidence_distribution", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_precision", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("top_verified", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rejected_examples", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(length=32), nullable=False, server_default="cre-v1"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("cre_rebuild_reports")
    op.drop_table("cre_admission_decisions")
    op.drop_table("cre_snapshots")
