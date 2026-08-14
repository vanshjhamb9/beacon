"""Beacon Observatory & Live Collector Runtime (BOLR) — Sprint 38.5.

Revision ID: 0058
Revises: 0057
Create Date: 2026-07-30

Tables:
    collector_runs — Collector execution history
    runtime_events — Live source feed events
    pipeline_trace — Pipeline tracing steps
    rejection_events — Rejection analysis records
    evidence_records — Evidence exploration records
    scheduler_history — Scheduler execution history
    runtime_metrics — Runtime performance metrics
    verification_logs — Dashboard verification logs
    bottleneck_snapshots — Bottleneck analysis snapshots
    alert_records — Observatory alerts
"""

revision = "20260730_0058"
down_revision = "20260730_0057"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

METADATA = sa.MetaData()

collector_runs = sa.Table(
    "collector_runs",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("connector", sa.String(128), nullable=False, index=True),
    sa.Column("run_number", sa.Integer, nullable=False),
    sa.Column("status", sa.String(32), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("duration_seconds", sa.Float, nullable=False, server_default="0"),
    sa.Column("signals_fetched", sa.Integer, nullable=False, server_default="0"),
    sa.Column("accepted", sa.Integer, nullable=False, server_default="0"),
    sa.Column("rejected", sa.Integer, nullable=False, server_default="0"),
    sa.Column("revenue_ready", sa.Integer, nullable=False, server_default="0"),
    sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
)

runtime_events = sa.Table(
    "runtime_events",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("event_type", sa.String(64), nullable=False, index=True),
    sa.Column("connector", sa.String(128), nullable=False, index=True),
    sa.Column("description", sa.Text, nullable=False, server_default=""),
    sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
)

pipeline_trace = sa.Table(
    "pipeline_trace",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("opportunity_id", sa.String(256), nullable=False, index=True),
    sa.Column("stage", sa.String(64), nullable=False, index=True),
    sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("duration_seconds", sa.Float, nullable=True),
    sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
)

rejection_events = sa.Table(
    "rejection_events",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("opportunity_id", sa.String(256), nullable=False, index=True),
    sa.Column("category", sa.String(64), nullable=False, index=True),
    sa.Column("reason", sa.Text, nullable=False, server_default=""),
    sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    sa.Column("source_connector", sa.String(128), nullable=True),
    sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
)

evidence_records = sa.Table(
    "evidence_records",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("opportunity_id", sa.String(256), nullable=False, index=True),
    sa.Column("evidence_type", sa.String(64), nullable=False),
    sa.Column("evidence_data", JSONB, nullable=False, server_default="{}"),
    sa.Column("source", sa.String(128), nullable=False, server_default=""),
    sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
    sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
)

scheduler_history = sa.Table(
    "scheduler_history",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("connector", sa.String(128), nullable=False, index=True),
    sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
    sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
)

runtime_metrics = sa.Table(
    "runtime_metrics",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("metric_name", sa.String(128), nullable=False, index=True),
    sa.Column("value", sa.Float, nullable=False),
    sa.Column("tags", JSONB, nullable=False, server_default="{}"),
    sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
)

verification_logs = sa.Table(
    "verification_logs",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("widget_name", sa.String(128), nullable=False, index=True),
    sa.Column("source_query", sa.Text, nullable=False, server_default=""),
    sa.Column("rows_returned", sa.Integer, nullable=False, server_default="0"),
    sa.Column("data_type", sa.String(32), nullable=False, server_default="unknown"),
    sa.Column("is_live", sa.Boolean, nullable=False, server_default="false"),
    sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
)

bottleneck_snapshots = sa.Table(
    "bottleneck_snapshots",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("stage", sa.String(64), nullable=False, index=True),
    sa.Column("count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("concentration", sa.Float, nullable=False, server_default="0"),
    sa.Column("avg_time_seconds", sa.Float, nullable=False, server_default="0"),
    sa.Column("severity", sa.String(32), nullable=False, server_default="none"),
    sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
)

alert_records = sa.Table(
    "alert_records",
    METADATA,
    sa.Column("id", UUID(as_uuid=False), primary_key=True),
    sa.Column("severity", sa.String(32), nullable=False, index=True),
    sa.Column("title", sa.String(256), nullable=False),
    sa.Column("message", sa.Text, nullable=False, server_default=""),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("resolved", sa.Boolean, nullable=False, server_default="false"),
    sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
)


def upgrade() -> None:
    for table in [
        collector_runs, runtime_events, pipeline_trace,
        rejection_events, evidence_records, scheduler_history,
        runtime_metrics, verification_logs, bottleneck_snapshots,
        alert_records,
    ]:
        op.create_table(table)


def downgrade() -> None:
    for table in reversed([
        collector_runs, runtime_events, pipeline_trace,
        rejection_events, evidence_records, scheduler_history,
        runtime_metrics, verification_logs, bottleneck_snapshots,
        alert_records,
    ]):
        op.drop_table(table)
