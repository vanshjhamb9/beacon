"""Create Discovery Quality Engine append-only tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260729_0054"
down_revision = "20260729_0053"
branch_labels = None
depends_on = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "quality_events",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("signal_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("source", sa.String(128), nullable=False, server_default=""),
        sa.Column("decision", sa.String(32), nullable=False, server_default=""),
        sa.Column("gates_passed", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("gates_failed", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rejection_reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_events_company_id", "quality_events", ["company_id"])
    op.create_index("ix_quality_events_decision_created", "quality_events", ["decision", "created_at"])
    op.create_index("ix_quality_events_source_created", "quality_events", ["source", "created_at"])
    op.create_index("ix_quality_events_signal_type_created", "quality_events", ["signal_type", "created_at"])

    op.create_table(
        "quality_decisions",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("signal_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("source", sa.String(128), nullable=False, server_default=""),
        sa.Column("decision", sa.String(32), nullable=False, server_default=""),
        sa.Column("gate_name", sa.String(64), nullable=False, server_default=""),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_decisions_company_id", "quality_decisions", ["company_id"])
    op.create_index("ix_quality_decisions_decision_created", "quality_decisions", ["decision", "created_at"])
    op.create_index("ix_quality_decisions_gate_created", "quality_decisions", ["gate_name", "created_at"])

    op.create_table(
        "quality_rejections",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("signal_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("source", sa.String(128), nullable=False, server_default=""),
        sa.Column("rejection_reason", sa.String(128), nullable=False, server_default=""),
        sa.Column("gate_name", sa.String(64), nullable=False, server_default=""),
        sa.Column("details", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_rejections_company_id", "quality_rejections", ["company_id"])
    op.create_index("ix_quality_rejections_reason_created", "quality_rejections", ["rejection_reason", "created_at"])
    op.create_index("ix_quality_rejections_gate_created", "quality_rejections", ["gate_name", "created_at"])

    op.create_table(
        "quality_snapshots",
        sa.Column("signals_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("signals_accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("signals_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("competitor_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("website_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("buying_signal_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_company_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icp_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("region_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_trust_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activity_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expired_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("connector_quality", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("top_rejection_reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_snapshots_created_at", "quality_snapshots", ["created_at"])

    op.create_table(
        "connector_quality",
        sa.Column("connector_name", sa.String(128), nullable=False),
        sa.Column("total_signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_quality_name", "connector_quality", ["connector_name"], unique=True)

    op.create_table(
        "company_quality",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("domain", sa.String(255), nullable=False, server_default=""),
        sa.Column("total_signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_signal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_company_quality_company_id", "company_quality", ["company_id"], unique=True)
    op.create_index("ix_company_quality_domain", "company_quality", ["domain"])

    op.create_table(
        "signal_quality",
        sa.Column("signal_type", sa.String(128), nullable=False),
        sa.Column("total_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_freshness_days", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_signal_quality_type", "signal_quality", ["signal_type"], unique=True)

    op.create_table(
        "quality_reports",
        sa.Column("report_type", sa.String(32), nullable=False, server_default=""),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptance_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_reports_type_date", "quality_reports", ["report_type", "report_date"], unique=True)


def downgrade() -> None:
    op.drop_table("quality_reports")
    op.drop_table("signal_quality")
    op.drop_table("company_quality")
    op.drop_table("connector_quality")
    op.drop_table("quality_snapshots")
    op.drop_table("quality_rejections")
    op.drop_table("quality_decisions")
    op.drop_table("quality_events")
