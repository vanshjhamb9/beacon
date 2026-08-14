"""Create Beacon Intelligence Center (BIC v1) append-only tables.

Revision 20260726_0049 follows operations center 0048.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260726_0049"
down_revision = "20260726_0048"
branch_labels = None
depends_on = None


def _base():
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "discovery_events",
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("collector", sa.String(64), nullable=True),
        sa.Column("connector", sa.String(64), nullable=True),
        sa.Column("status", sa.String(64), nullable=True),
        sa.Column("headline", sa.Text(), nullable=False, server_default=""),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("is_error", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_revenue_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_discovery_events_event_type", "discovery_events", ["event_type"])
    op.create_index("ix_discovery_events_created_at", "discovery_events", ["created_at"])
    op.create_index("ix_discovery_events_occurred_at", "discovery_events", ["occurred_at"])
    op.create_index("ix_discovery_events_company_id", "discovery_events", ["company_id"])
    op.create_index("ix_discovery_events_collector", "discovery_events", ["collector"])
    op.create_index("ix_discovery_events_connector", "discovery_events", ["connector"])
    op.create_index("ix_discovery_events_dedupe_key", "discovery_events", ["dedupe_key"], unique=True)
    op.create_index(
        "ix_discovery_events_event_type_created",
        "discovery_events",
        ["event_type", "created_at"],
    )

    op.create_table(
        "company_journey_events",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="completed"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("connector", sa.String(64), nullable=True),
        sa.Column("worker", sa.String(64), nullable=True),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failures", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_company_journey_events_company_id", "company_journey_events", ["company_id"])
    op.create_index("ix_company_journey_events_stage", "company_journey_events", ["stage"])
    op.create_index("ix_company_journey_events_occurred_at", "company_journey_events", ["occurred_at"])
    op.create_index("ix_company_journey_events_dedupe_key", "company_journey_events", ["dedupe_key"], unique=True)
    op.create_index(
        "ix_company_journey_events_company_stage",
        "company_journey_events",
        ["company_id", "stage"],
    )

    op.create_table(
        "connector_roi_daily",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("healthy", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("api_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("quota_used_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index(
        "ix_connector_roi_daily_connector_date",
        "connector_roi_daily",
        ["connector", "report_date"],
        unique=True,
    )

    op.create_table(
        "dataset_statistics_daily",
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("signals_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spam", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dead_websites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("working_websites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generic_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("founder_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outreach_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("spam_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("verification_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("enrichment_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index(
        "ix_dataset_statistics_daily_report_date",
        "dataset_statistics_daily",
        ["report_date"],
        unique=True,
    )

    op.create_table(
        "pipeline_replay_frames",
        sa.Column("hour_key", sa.String(32), nullable=False),
        sa.Column("frame_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("websites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contacted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("movements", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_pipeline_replay_frames_hour_key", "pipeline_replay_frames", ["hour_key"], unique=True)
    op.create_index("ix_pipeline_replay_frames_frame_at", "pipeline_replay_frames", ["frame_at"])


def downgrade() -> None:
    op.drop_table("pipeline_replay_frames")
    op.drop_table("dataset_statistics_daily")
    op.drop_table("connector_roi_daily")
    op.drop_table("company_journey_events")
    op.drop_table("discovery_events")
