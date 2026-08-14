"""Create Opportunity Connector Platform append-only tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260729_0052"
down_revision = "20260728_0051"
branch_labels = None
depends_on = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "connector_registry",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("configured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("healthy", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("capabilities", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("average_latency", sa.Float(), nullable=False, server_default="0"),
        sa.Column("failure_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rate_limit_remaining", sa.Integer(), nullable=True),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("events_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_registry_connector_id", "connector_registry", ["connector_id"], unique=True)
    op.create_index("ix_connector_registry_enabled", "connector_registry", ["enabled"])

    op.create_table(
        "connector_runs",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("total_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_runs_connector_id", "connector_runs", ["connector_id"])
    op.create_index("ix_connector_runs_status", "connector_runs", ["status"])
    op.create_index("ix_connector_runs_created_at", "connector_runs", ["created_at"])

    op.create_table(
        "connector_events",
        sa.Column("event_id", UUID(as_uuid=True), nullable=False),
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("connector_version", sa.String(32), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("headline", sa.String(512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("event_category", sa.String(64), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country", sa.String(16), nullable=True),
        sa.Column("language", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rejection_reason", sa.String(128), nullable=True),
        sa.Column("raw_metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("collector", sa.String(128), nullable=False),
        sa.Column("routed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("route", sa.String(128), nullable=False, server_default="live_opportunity_discovery"),
        *_base(),
    )
    op.create_index("ix_connector_events_connector_id", "connector_events", ["connector_id"])
    op.create_index("ix_connector_events_event_type", "connector_events", ["event_type"])
    op.create_index("ix_connector_events_published_at", "connector_events", ["published_at"])
    op.create_index("ix_connector_events_accepted", "connector_events", ["accepted"])
    op.create_index("ix_connector_events_company", "connector_events", ["company_name"])

    op.create_table(
        "connector_statistics",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("period", sa.String(32), nullable=False),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("identity_matched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contacted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("signal_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_per_signal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_statistics_connector_id", "connector_statistics", ["connector_id"])
    op.create_index("ix_connector_statistics_period", "connector_statistics", ["period"])

    op.create_table(
        "connector_health",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("authenticated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rate_limit_remaining", sa.Integer(), nullable=True),
        sa.Column("queue_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("freshness_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_success", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_health_connector_id", "connector_health", ["connector_id"], unique=True)
    op.create_index("ix_connector_health_status", "connector_health", ["status"])

    op.create_table(
        "connector_yield",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("identity_matched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contacted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("signal_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_per_signal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_yield_connector_id", "connector_yield", ["connector_id"], unique=True)

    op.create_table(
        "connector_configuration",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="normal"),
        sa.Column("rate_limit", sa.String(128), nullable=False, server_default="unknown"),
        sa.Column("authentication", sa.String(32), nullable=False, server_default="none"),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_concurrency", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("dependencies", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("retry_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("retry_backoff_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_configuration_connector_id", "connector_configuration", ["connector_id"], unique=True)

    op.create_table(
        "connector_failures",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("error_type", sa.String(128), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_failures_connector_id", "connector_failures", ["connector_id"])
    op.create_index("ix_connector_failures_error_type", "connector_failures", ["error_type"])

    op.create_table(
        "connector_rate_limits",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remaining", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_rate_limits_connector_id", "connector_rate_limits", ["connector_id"], unique=True)

    op.create_table(
        "connector_capabilities",
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("event_types", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("emits_evidence_only", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_incremental_sync", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("supports_historical", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("max_batch_size", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("requires_authentication", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_capabilities_connector_id", "connector_capabilities", ["connector_id"], unique=True)


def downgrade() -> None:
    op.drop_table("connector_capabilities")
    op.drop_table("connector_rate_limits")
    op.drop_table("connector_failures")
    op.drop_table("connector_configuration")
    op.drop_table("connector_yield")
    op.drop_table("connector_health")
    op.drop_table("connector_statistics")
    op.drop_table("connector_events")
    op.drop_table("connector_runs")
    op.drop_table("connector_registry")
