"""Create revenue operations center tables.

Revision ID: 20260724_0024
Revises: 20260723_0023
Create Date: 2026-07-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0024"
down_revision: str | None = "20260723_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "revenue_operation_snapshots",
        *_base(),
        sa.Column("revenue_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pipeline_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="roc-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_operation_snapshots")),
    )
    op.create_index("ix_roc_snapshots_created", "revenue_operation_snapshots", ["created_at"])

    op.create_table(
        "revenue_alerts",
        *_base(),
        sa.Column("alert_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False, server_default="medium"),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("lifecycle", sa.String(32), nullable=False, server_default="new"),
        sa.Column("dedupe_key", sa.String(128), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_revenue_alerts_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["revenue_operation_snapshots.id"],
            name=op.f("fk_revenue_alerts_snapshot_id_revenue_operation_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_alerts")),
    )
    op.create_index("ix_roc_alerts_lifecycle_created", "revenue_alerts", ["lifecycle", "created_at"])
    op.create_index("ix_roc_alerts_dedupe", "revenue_alerts", ["dedupe_key"])

    op.create_table(
        "revenue_forecasts",
        *_base(),
        sa.Column("this_week", sa.Float(), nullable=False, server_default="0"),
        sa.Column("this_month", sa.Float(), nullable=False, server_default="0"),
        sa.Column("quarter", sa.Float(), nullable=False, server_default="0"),
        sa.Column("annual", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pipeline_health", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="roc-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_forecasts")),
    )
    op.create_index("ix_roc_forecasts_created", "revenue_forecasts", ["created_at"])

    op.create_table(
        "revenue_memory",
        *_base(),
        sa.Column("record_type", sa.String(64), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", _json(), nullable=False),
        sa.Column("searchable_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_revenue_memory_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_memory")),
    )
    op.create_index("ix_roc_memory_type_created", "revenue_memory", ["record_type", "created_at"])
    op.create_index("ix_roc_memory_company", "revenue_memory", ["company_id"])

    op.create_table(
        "revenue_replays",
        *_base(),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=True),
        sa.Column("events", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="roc-v1"),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_revenue_replays_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_revenue_replays_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_replays")),
    )
    op.create_index("ix_roc_replays_company", "revenue_replays", ["company_id"])
    op.create_index("ix_roc_replays_opportunity", "revenue_replays", ["opportunity_id"])

    op.create_table(
        "revenue_operation_metrics",
        *_base(),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("close_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="roc-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_operation_metrics")),
    )
    op.create_index("ix_roc_metrics_created", "revenue_operation_metrics", ["created_at"])

    op.create_table(
        "revenue_operation_learning",
        *_base(),
        sa.Column("recommendation_id", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_approval"),
        sa.Column("modifies_production", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_operation_learning")),
    )
    op.create_index("ix_roc_learning_status_created", "revenue_operation_learning", ["status", "created_at"])
    op.create_index("ix_roc_learning_rec_id", "revenue_operation_learning", ["recommendation_id"])

    op.create_table(
        "agency_statistics",
        *_base(),
        sa.Column("kind", sa.String(64), nullable=False, server_default="daily"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="roc-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agency_statistics")),
    )
    op.create_index("ix_roc_agency_stats_created", "agency_statistics", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_roc_agency_stats_created", table_name="agency_statistics")
    op.drop_table("agency_statistics")
    op.drop_index("ix_roc_learning_rec_id", table_name="revenue_operation_learning")
    op.drop_index("ix_roc_learning_status_created", table_name="revenue_operation_learning")
    op.drop_table("revenue_operation_learning")
    op.drop_index("ix_roc_metrics_created", table_name="revenue_operation_metrics")
    op.drop_table("revenue_operation_metrics")
    op.drop_index("ix_roc_replays_opportunity", table_name="revenue_replays")
    op.drop_index("ix_roc_replays_company", table_name="revenue_replays")
    op.drop_table("revenue_replays")
    op.drop_index("ix_roc_memory_company", table_name="revenue_memory")
    op.drop_index("ix_roc_memory_type_created", table_name="revenue_memory")
    op.drop_table("revenue_memory")
    op.drop_index("ix_roc_forecasts_created", table_name="revenue_forecasts")
    op.drop_table("revenue_forecasts")
    op.drop_index("ix_roc_alerts_dedupe", table_name="revenue_alerts")
    op.drop_index("ix_roc_alerts_lifecycle_created", table_name="revenue_alerts")
    op.drop_table("revenue_alerts")
    op.drop_index("ix_roc_snapshots_created", table_name="revenue_operation_snapshots")
    op.drop_table("revenue_operation_snapshots")
