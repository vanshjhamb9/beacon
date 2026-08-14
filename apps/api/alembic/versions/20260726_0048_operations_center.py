"""Create Beacon Operations Center (BOC v1) tables.

Note: Sprint brief referenced revision 20260725_0043; that id is already used by ODU
(20260724_0043). This append-only revision is 20260726_0048 after execution readiness 0047.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260726_0048"
down_revision = "20260726_0047"
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
        "pipeline_stage_metrics",
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hour", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_pipeline_stage_metrics_stage", "pipeline_stage_metrics", ["stage"])
    op.create_index(
        "ix_pipeline_stage_metrics_stage_created",
        "pipeline_stage_metrics",
        ["stage", "created_at"],
    )

    op.create_table(
        "connector_health",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("healthy", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure", sa.DateTime(timezone=True), nullable=True),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_runtime", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rate_limited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_health_connector", "connector_health", ["connector"], unique=True)

    op.create_table(
        "worker_health",
        sa.Column("worker_name", sa.String(64), nullable=False),
        sa.Column("running", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("queue_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_duration", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_execution", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_worker_health_worker_name", "worker_health", ["worker_name"], unique=True)

    op.create_table(
        "operation_snapshots",
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_operation_snapshots_created_at", "operation_snapshots", ["created_at"])

    op.create_table(
        "ingestion_events",
        sa.Column("collector", sa.String(64), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_ingestion_events_collector", "ingestion_events", ["collector"])
    op.create_index("ix_ingestion_events_status", "ingestion_events", ["status"])
    op.create_index(
        "ix_ingestion_events_collector_created",
        "ingestion_events",
        ["collector", "created_at"],
    )
    op.create_index(
        "ix_ingestion_events_status_created",
        "ingestion_events",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("ingestion_events")
    op.drop_table("operation_snapshots")
    op.drop_table("worker_health")
    op.drop_table("connector_health")
    op.drop_table("pipeline_stage_metrics")
