"""Create revenue execution validation tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0039"
down_revision = "20260724_0038"
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
        "rev_evaluations",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("is_revenue_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rev-v1"),
        *_base(),
    )
    op.create_index("ix_rev_evaluations_company_id", "rev_evaluations", ["company_id"])
    op.create_index("ix_rev_evaluations_ready", "rev_evaluations", ["is_revenue_ready"])

    op.create_table(
        "rev_rejection_records",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("reasons", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rev_rejection_records_source", "rev_rejection_records", ["source"])

    op.create_table(
        "rev_funnel_snapshots",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("founder_queue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rev-v1"),
        *_base(),
    )

    op.create_table(
        "rev_connector_scores",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("grade", sa.String(32), nullable=False),
        sa.Column("revenue_ready_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rev_connector_scores_connector", "rev_connector_scores", ["connector"])

    op.create_table(
        "rev_founder_queue_cards",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rev-v1"),
        *_base(),
    )

    op.create_table(
        "rev_manual_qa",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("rating", sa.String(64), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rev_manual_qa_rating", "rev_manual_qa", ["rating"])

    op.create_table(
        "rev_daily_reports",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rev-v1"),
        *_base(),
    )

    op.create_table(
        "rev_acceptance_gates",
        sa.Column("production_unlocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("failures", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rev-v1"),
        *_base(),
    )


def downgrade() -> None:
    for t in (
        "rev_acceptance_gates",
        "rev_daily_reports",
        "rev_manual_qa",
        "rev_founder_queue_cards",
        "rev_connector_scores",
        "rev_funnel_snapshots",
        "rev_rejection_records",
        "rev_evaluations",
    ):
        op.drop_table(t)
