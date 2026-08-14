"""Create Live Revenue Operations Platform (LROP) tables — Sprint 38.

Tables:
    opportunity_inbox — New opportunities awaiting review
    opportunity_stage_history — Append-only stage transitions
    founder_reviews — Human review decisions
    pipeline_snapshots — Pipeline state snapshots
    connector_roi — Connector ROI tracking
    opportunity_aging — Opportunity aging data
    live_feed — Live discovery feed events
    bulk_actions — Bulk operation records
    data_hygiene — Data hygiene issues
    revenue_operations_reports — Generated reports
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260730_0057"
down_revision = "20260729_0056"
branch_labels = None
depends_on = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    # Get existing tables to avoid duplicates
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "opportunity_inbox" not in existing_tables:
        op.create_table(
            "opportunity_inbox",
            sa.Column("opportunity_id", sa.String(128), nullable=False),
            sa.Column("company_name", sa.String(255), nullable=False, server_default="unknown"),
            sa.Column("website", sa.Text(), nullable=False, server_default="unknown"),
            sa.Column("buying_signal", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("connector", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("signal_age_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("why_now", sa.Text(), nullable=False, server_default="unknown"),
            sa.Column("revenue_potential", sa.String(32), nullable=False, server_default="unknown"),
            sa.Column("status", sa.String(32), nullable=False, server_default="new"),
            sa.Column("assigned_to", sa.String(64), nullable=False, server_default="unassigned"),
            sa.Column("tags", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("notes", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_base(),
        )
        op.create_index("ix_opportunity_inbox_opportunity_id", "opportunity_inbox", ["opportunity_id"])
        op.create_index("ix_opportunity_inbox_status_created", "opportunity_inbox", ["status", "created_at"])
        op.create_index("ix_opportunity_inbox_connector_created", "opportunity_inbox", ["connector", "created_at"])

    if "opportunity_stage_history" not in existing_tables:
        op.create_table(
            "opportunity_stage_history",
            sa.Column("opportunity_id", sa.String(128), nullable=False),
            sa.Column("from_stage", sa.String(32), nullable=False, server_default=""),
            sa.Column("to_stage", sa.String(32), nullable=False, server_default=""),
            sa.Column("action", sa.String(64), nullable=False, server_default=""),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("actor", sa.String(64), nullable=False, server_default="system"),
            sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
            *_base(),
        )
        op.create_index("ix_opportunity_stage_history_opportunity_id", "opportunity_stage_history", ["opportunity_id"])
        op.create_index("ix_opportunity_stage_history_to_stage_created", "opportunity_stage_history", ["to_stage", "created_at"])

    if "founder_reviews" not in existing_tables:
        op.create_table(
            "founder_reviews",
            sa.Column("opportunity_id", sa.String(128), nullable=False),
            sa.Column("reviewer", sa.String(64), nullable=False, server_default="founder"),
            sa.Column("decision", sa.String(32), nullable=True),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration_seconds", sa.Float(), nullable=True),
            *_base(),
        )
        op.create_index("ix_founder_reviews_opportunity_id", "founder_reviews", ["opportunity_id"])
        op.create_index("ix_founder_reviews_decision_created", "founder_reviews", ["decision", "created_at"])

    if "pipeline_snapshots" not in existing_tables:
        op.create_table(
            "pipeline_snapshots",
            sa.Column("snapshot_date", sa.Date(), nullable=False),
            sa.Column("pipeline_data", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("metrics", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_base(),
        )
        op.create_index("ix_pipeline_snapshots_snapshot_date", "pipeline_snapshots", ["snapshot_date"])

    if "connector_roi" not in existing_tables:
        op.create_table(
            "connector_roi",
            sa.Column("connector_name", sa.String(64), nullable=False),
            sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("validated", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contacted", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("customers", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("revenue", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("cost", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("recommendation", sa.String(32), nullable=False, server_default="unknown"),
            *_base(),
        )
        op.create_index("ix_connector_roi_connector_name", "connector_roi", ["connector_name"])

    if "opportunity_aging" not in existing_tables:
        op.create_table(
            "opportunity_aging",
            sa.Column("opportunity_id", sa.String(128), nullable=False),
            sa.Column("signal_type", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("current_stage", sa.String(32), nullable=False, server_default="new"),
            sa.Column("age_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("color", sa.String(16), nullable=False, server_default="green"),
            sa.Column("is_expired", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
            *_base(),
        )
        op.create_index("ix_opportunity_aging_opportunity_id", "opportunity_aging", ["opportunity_id"])
        op.create_index("ix_opportunity_aging_color_created", "opportunity_aging", ["color", "created_at"])

    if "live_feed" not in existing_tables:
        op.create_table(
            "live_feed",
            sa.Column("event_type", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("source", sa.String(128), nullable=False, server_default="unknown"),
            sa.Column("connector", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("company_name", sa.String(255), nullable=False, server_default="unknown"),
            sa.Column("buying_signal", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("stage", sa.String(32), nullable=False, server_default="unknown"),
            sa.Column("status", sa.String(32), nullable=False, server_default="unknown"),
            sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
            *_base(),
        )
        op.create_index("ix_live_feed_event_timestamp", "live_feed", ["event_timestamp"])
        op.create_index("ix_live_feed_connector_created", "live_feed", ["connector", "created_at"])

    if "bulk_actions" not in existing_tables:
        op.create_table(
            "bulk_actions",
            sa.Column("action_type", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("opportunity_ids", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("result", sa.String(32), nullable=False, server_default="unknown"),
            sa.Column("actor", sa.String(64), nullable=False, server_default="system"),
            sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_base(),
        )
        op.create_index("ix_bulk_actions_action_type_created", "bulk_actions", ["action_type", "created_at"])

    if "data_hygiene" not in existing_tables:
        op.create_table(
            "data_hygiene",
            sa.Column("issue_type", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("opportunity_id", sa.String(128), nullable=True),
            sa.Column("company_name", sa.String(255), nullable=True),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("severity", sa.String(16), nullable=False, server_default="low"),
            sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            *_base(),
        )
        op.create_index("ix_data_hygiene_issue_type_created", "data_hygiene", ["issue_type", "created_at"])
        op.create_index("ix_data_hygiene_resolved_created", "data_hygiene", ["resolved", "created_at"])

    if "revenue_operations_reports" not in existing_tables:
        op.create_table(
            "revenue_operations_reports",
            sa.Column("report_type", sa.String(64), nullable=False, server_default="unknown"),
            sa.Column("title", sa.String(255), nullable=False, server_default=""),
            sa.Column("report_data", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            *_base(),
        )
        op.create_index("ix_revenue_operations_reports_report_type", "revenue_operations_reports", ["report_type"])


def downgrade() -> None:
    op.drop_table("revenue_operations_reports")
    op.drop_table("data_hygiene")
    op.drop_table("bulk_actions")
    op.drop_table("live_feed")
    op.drop_table("opportunity_aging")
    op.drop_table("connector_roi")
    op.drop_table("pipeline_snapshots")
    op.drop_table("founder_reviews")
    op.drop_table("opportunity_stage_history")
    op.drop_table("opportunity_inbox")
