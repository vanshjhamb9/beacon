"""Create Closed Loop Revenue Validation (CLR v1) tables.

Note: Sprint brief referenced revision 20260725_0043; alembic chain already used
20260724_0043 for ODU, so this append-only revision is 20260725_0046 after OFC 0045.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260725_0046"
down_revision = "20260724_0045"
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
        "clr_outcome_events",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outreach_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(64), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor", sa.String(128), nullable=False, server_default="founder"),
        sa.Column("source", sa.String(64), nullable=False, server_default="clr"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("previous_state", sa.String(64), nullable=True),
        sa.Column("new_state", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_clr_outcome_events_company_id", "clr_outcome_events", ["company_id"])
    op.create_index("ix_clr_outcome_events_outcome", "clr_outcome_events", ["outcome"])

    op.create_table(
        "clr_daily_briefs",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("today_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="clr-v1"),
        *_base(),
    )

    op.create_table(
        "clr_weekly_reviews",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="clr-v1"),
        *_base(),
    )

    op.create_table(
        "clr_revenue_events",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False, server_default=""),
        sa.Column("service_sold", sa.String(256), nullable=False, server_default=""),
        sa.Column("revenue_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("close_date", sa.String(32), nullable=True),
        sa.Column("sales_cycle_days", sa.Float(), nullable=True),
        sa.Column("proposal_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("actual_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("founder", sa.String(128), nullable=False, server_default="Vansh"),
        sa.Column("source_connector", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("revenue_ready_snapshot_id", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_clr_revenue_events_company_id", "clr_revenue_events", ["company_id"])

    op.create_table(
        "clr_prediction_validation",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False, server_default=""),
        sa.Column("interested", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("decision_maker_correct", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("why_now_accurate", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("service_accepted", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("confidence_realistic", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_clr_prediction_validation_company_id", "clr_prediction_validation", ["company_id"])

    op.create_table(
        "clr_learning_metrics",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="clr-v1"),
        *_base(),
    )

    op.create_table(
        "clr_pipeline_snapshots",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="clr-v1"),
        *_base(),
    )

    op.create_table(
        "clr_founder_actions",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_clr_founder_actions_company_id", "clr_founder_actions", ["company_id"])


def downgrade() -> None:
    op.drop_table("clr_founder_actions")
    op.drop_table("clr_pipeline_snapshots")
    op.drop_table("clr_learning_metrics")
    op.drop_table("clr_prediction_validation")
    op.drop_table("clr_revenue_events")
    op.drop_table("clr_weekly_reviews")
    op.drop_table("clr_daily_briefs")
    op.drop_table("clr_outcome_events")
