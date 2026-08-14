"""Create signal collection tables.

Revision ID: 20260710_0001
Revises:
Create Date: 2026-07-10 15:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    raw_event_status = postgresql.ENUM(
        "RECEIVED",
        "PROCESSED",
        "REJECTED",
        name="raw_event_status",
        create_type=False,
    )
    source_health_status = postgresql.ENUM(
        "HEALTHY",
        "DEGRADED",
        "DOWN",
        name="source_health_status",
        create_type=False,
    )
    postgresql.ENUM("RECEIVED", "PROCESSED", "REJECTED", name="raw_event_status").create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM("HEALTHY", "DEGRADED", "DOWN", name="source_health_status").create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "raw_events",
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("stream_id", sa.String(length=128), nullable=True),
        sa.Column("status", raw_event_status, nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_events")),
        sa.UniqueConstraint("idempotency_key", name="uq_raw_events_idempotency_key"),
    )
    op.create_index("ix_raw_events_event_hash", "raw_events", ["event_hash"])
    op.create_index("ix_raw_events_source_published_at", "raw_events", ["source", "published_at"])
    op.create_index("ix_raw_events_url", "raw_events", ["url"])

    op.create_table(
        "source_health",
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("status", source_health_status, nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("average_latency_ms", sa.Float(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_health")),
        sa.UniqueConstraint("source", name="uq_source_health_source"),
    )


def downgrade() -> None:
    op.drop_table("source_health")
    op.drop_index("ix_raw_events_url", table_name="raw_events")
    op.drop_index("ix_raw_events_source_published_at", table_name="raw_events")
    op.drop_index("ix_raw_events_event_hash", table_name="raw_events")
    op.drop_table("raw_events")

    postgresql.ENUM(name="source_health_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="raw_event_status").drop(op.get_bind(), checkfirst=True)
