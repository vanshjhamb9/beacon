"""Create Operation Dataset Unlock tables (odu-v1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0043"
down_revision = "20260724_0042"
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
        "odu_connector_health",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("health", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_odu_connector_health_connector", "odu_connector_health", ["connector"])

    op.create_table(
        "odu_source_tokens",
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("env_key", sa.String(128), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )

    op.create_table(
        "odu_connector_metrics",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("websites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yield_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )

    op.create_table(
        "odu_daily_reports",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("business_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vansh_ready_answer", sa.String(8), nullable=False, server_default="NO"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="odu-v1"),
        *_base(),
    )

    op.create_table(
        "odu_recovery_queue",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_odu_recovery_queue_status", "odu_recovery_queue", ["status"])

    op.create_table(
        "odu_operation_logs",
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )


def downgrade() -> None:
    for t in (
        "odu_operation_logs",
        "odu_recovery_queue",
        "odu_daily_reports",
        "odu_connector_metrics",
        "odu_source_tokens",
        "odu_connector_health",
    ):
        op.drop_table(t)
