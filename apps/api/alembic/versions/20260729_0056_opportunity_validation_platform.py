"""Create Live Opportunity Validation Platform (LOVP) tables — Sprint 37.5.

Tables:
    validation_outcomes — Validation decisions for opportunities
    validation_audit_trail — Full audit trail of validation gates
    signal_traces — Signal origin and lifecycle tracking
    company_traces — Company discovery history
    connector_traces — Connector performance tracking
    opportunity_timelines — Timeline events for opportunities
    human_reviews — Human reviewer decisions
    validation_metrics — Aggregated validation statistics
    validation_reports — Generated validation reports
    replay_results — Replay engine results
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260729_0056"
down_revision = "20260729_0055"
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
        "validation_outcomes",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default="unknown"),
        sa.Column("decision", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("validator", sa.String(64), nullable=False, server_default="system"),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("root_cause", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("human_verdict", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_validation_outcomes_opportunity_id", "validation_outcomes", ["opportunity_id"])
    op.create_index("ix_validation_outcomes_decision_created", "validation_outcomes", ["decision", "created_at"])
    op.create_index("ix_validation_outcomes_root_cause_created", "validation_outcomes", ["root_cause", "created_at"])

    op.create_table(
        "validation_audit_trail",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("gate", sa.String(64), nullable=False, server_default=""),
        sa.Column("decision", sa.String(32), nullable=False, server_default=""),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_validation_audit_trail_opportunity_id", "validation_audit_trail", ["opportunity_id"])
    op.create_index("ix_validation_audit_trail_gate_created", "validation_audit_trail", ["gate", "created_at"])

    op.create_table(
        "signal_traces",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("signal_type", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("signal_source", sa.String(128), nullable=False, server_default="unknown"),
        sa.Column("connector", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("original_url", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("original_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collection_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("origin", sa.String(32), nullable=False, server_default="connector"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_signal_traces_opportunity_id", "signal_traces", ["opportunity_id"])
    op.create_index("ix_signal_traces_connector_created", "signal_traces", ["connector", "created_at"])
    op.create_index("ix_signal_traces_signal_type_created", "signal_traces", ["signal_type", "created_at"])

    op.create_table(
        "company_traces",
        sa.Column("company_id", sa.String(128), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default="unknown"),
        sa.Column("website", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("industry", sa.String(128), nullable=False, server_default="unknown"),
        sa.Column("country", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("discovery_source", sa.String(128), nullable=False, server_default="unknown"),
        sa.Column("discovery_connector", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("discovery_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_evidence_url", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("validation_history", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("current_state", sa.String(32), nullable=False, server_default="discovered"),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_company_traces_company_id", "company_traces", ["company_id"])
    op.create_index("ix_company_traces_current_state_created", "company_traces", ["current_state", "created_at"])
    op.create_index("ix_company_traces_discovery_connector_created", "company_traces", ["discovery_connector", "created_at"])

    op.create_table(
        "connector_traces",
        sa.Column("connector_name", sa.String(64), nullable=False),
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default="unknown"),
        sa.Column("signal_type", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("signal_quality", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("validation_decision", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_connector_traces_connector_name", "connector_traces", ["connector_name"])
    op.create_index("ix_connector_traces_opportunity_id", "connector_traces", ["opportunity_id"])

    op.create_table(
        "opportunity_timelines",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("description", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("source", sa.String(128), nullable=False, server_default="unknown"),
        sa.Column("connector", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_opportunity_timelines_opportunity_id", "opportunity_timelines", ["opportunity_id"])
    op.create_index("ix_opportunity_timelines_event_type_created", "opportunity_timelines", ["event_type", "created_at"])

    op.create_table(
        "human_reviews",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("reviewer", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_human_reviews_opportunity_id", "human_reviews", ["opportunity_id"])
    op.create_index("ix_human_reviews_decision_created", "human_reviews", ["decision", "created_at"])
    op.create_index("ix_human_reviews_reviewer_created", "human_reviews", ["reviewer", "created_at"])

    op.create_table(
        "validation_metrics",
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("metric_value", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_validation_metrics_metric_key", "validation_metrics", ["metric_key"])

    op.create_table(
        "validation_reports",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("report_data", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_validation_reports_opportunity_id", "validation_reports", ["opportunity_id"])

    op.create_table(
        "replay_results",
        sa.Column("opportunity_id", sa.String(128), nullable=False),
        sa.Column("replay_data", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
    )
    op.create_index("ix_replay_results_opportunity_id", "replay_results", ["opportunity_id"])


def downgrade() -> None:
    op.drop_table("replay_results")
    op.drop_table("validation_reports")
    op.drop_table("validation_metrics")
    op.drop_table("human_reviews")
    op.drop_table("opportunity_timelines")
    op.drop_table("connector_traces")
    op.drop_table("company_traces")
    op.drop_table("signal_traces")
    op.drop_table("validation_audit_trail")
    op.drop_table("validation_outcomes")
