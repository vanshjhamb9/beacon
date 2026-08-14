"""Create identity coverage expansion tables (ice-v1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0041"
down_revision = "20260724_0040"
branch_labels = None
depends_on = None


def _base():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "identity_coverage_snapshots",
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("admitted_hint", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="ice-v1"),
        *_base(),
    )
    op.create_index("ix_identity_coverage_snapshots_signal", "identity_coverage_snapshots", ["signal_id"])
    op.create_index("ix_identity_coverage_snapshots_domain", "identity_coverage_snapshots", ["domain"])

    op.create_table(
        "identity_provider_results",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity_coverage_snapshots.id"), nullable=True),
        sa.Column("provider", sa.String(128), nullable=False),
        sa.Column("field", sa.String(64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("collector", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_identity_provider_results_provider", "identity_provider_results", ["provider"])

    op.create_table(
        "identity_alias_graph",
        sa.Column("primary_name", sa.String(255), nullable=False),
        sa.Column("normalized_key", sa.String(255), nullable=False),
        sa.Column("aliases", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("official_domain", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("merge_evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_identity_alias_graph_normalized", "identity_alias_graph", ["normalized_key"])
    op.create_index("ix_identity_alias_graph_domain", "identity_alias_graph", ["official_domain"])

    op.create_table(
        "identity_domain_intelligence",
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("dns_ok", sa.Boolean(), nullable=True),
        sa.Column("ssl_ok", sa.Boolean(), nullable=True),
        sa.Column("mx", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base(),
    )
    op.create_index("ix_identity_domain_intelligence_domain", "identity_domain_intelligence", ["domain"])

    op.create_table(
        "identity_collector_metrics",
        sa.Column("collector", sa.String(64), nullable=False),
        sa.Column("recommendation", sa.String(32), nullable=False, server_default="KEEP"),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("official_websites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("business_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("identity_precision", sa.Float(), nullable=False, server_default="0"),
        sa.Column("identity_recall", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_identity_collector_metrics_collector", "identity_collector_metrics", ["collector"])

    op.create_table(
        "identity_recovery_queue",
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_identity_recovery_queue_status", "identity_recovery_queue", ["status"])
    op.create_index("ix_identity_recovery_queue_reason", "identity_recovery_queue", ["reason"])

    op.create_table(
        "identity_daily_reports",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("coverage_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vansh_ready_answer", sa.String(8), nullable=False, server_default="NO"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="ice-v1"),
        *_base(),
    )


def downgrade() -> None:
    for t in (
        "identity_daily_reports",
        "identity_recovery_queue",
        "identity_collector_metrics",
        "identity_domain_intelligence",
        "identity_alias_graph",
        "identity_provider_results",
        "identity_coverage_snapshots",
    ):
        op.drop_table(t)
