"""Create founder revenue OS tables.

Revision ID: 20260723_0018
Revises: 20260723_0017
Create Date: 2026-07-23 17:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0018"
down_revision: str | None = "20260723_0017"
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
        "founder_daily_briefs",
        *_base(),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("new_companies_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_buying_signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qualified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready_accounts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("a_plus_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("campaigns_waiting_approval", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies_waiting", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("proposals_pending", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_pipeline", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("lost_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("top_performing_industry", sa.String(128), nullable=True),
        sa.Column("top_performing_service", sa.String(128), nullable=True),
        sa.Column("top_performing_outreach_style", sa.String(128), nullable=True),
        sa.Column("top_performing_subject_line", sa.String(255), nullable=True),
        sa.Column("top_performing_cta", sa.String(255), nullable=True),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="fos-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_founder_daily_briefs")),
    )
    op.create_index("ix_founder_daily_briefs_created", "founder_daily_briefs", ["created_at"])

    op.create_table(
        "founder_revenue_tasks",
        *_base(),
        sa.Column("task_key", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("priority", sa.String(8), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner", sa.String(128), nullable=False, server_default="founder"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("related_id", sa.String(128), nullable=True),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_founder_revenue_tasks_company_id_companies")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_founder_revenue_tasks")),
    )
    op.create_index("ix_founder_tasks_status_priority", "founder_revenue_tasks", ["status", "priority"])
    op.create_index("ix_founder_tasks_company", "founder_revenue_tasks", ["company_id"])

    op.create_table(
        "founder_timeline_events",
        *_base(),
        sa.Column("event_key", sa.String(64), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_founder_timeline_events_company_id_companies")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_founder_timeline_events")),
    )
    op.create_index("ix_founder_timeline_company_occurred", "founder_timeline_events", ["company_id", "occurred_at"])
    op.create_index("ix_founder_timeline_stage", "founder_timeline_events", ["stage"])

    op.create_table(
        "founder_analytics_events",
        *_base(),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False, server_default="founder"),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(64), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_founder_analytics_events")),
    )
    op.create_index("ix_founder_analytics_type_created", "founder_analytics_events", ["event_type", "created_at"])
    op.create_index("ix_founder_analytics_company", "founder_analytics_events", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_founder_analytics_company", table_name="founder_analytics_events")
    op.drop_index("ix_founder_analytics_type_created", table_name="founder_analytics_events")
    op.drop_table("founder_analytics_events")
    op.drop_index("ix_founder_timeline_stage", table_name="founder_timeline_events")
    op.drop_index("ix_founder_timeline_company_occurred", table_name="founder_timeline_events")
    op.drop_table("founder_timeline_events")
    op.drop_index("ix_founder_tasks_company", table_name="founder_revenue_tasks")
    op.drop_index("ix_founder_tasks_status_priority", table_name="founder_revenue_tasks")
    op.drop_table("founder_revenue_tasks")
    op.drop_index("ix_founder_daily_briefs_created", table_name="founder_daily_briefs")
    op.drop_table("founder_daily_briefs")
