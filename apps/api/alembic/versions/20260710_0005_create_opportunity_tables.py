"""Create opportunity engine tables.

Revision ID: 20260710_0005
Revises: 20260710_0004
Create Date: 2026-07-10 19:08:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0005"
down_revision: str | None = "20260710_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("recommendation", sa.String(64), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("timing_score", sa.Float(), nullable=False),
        sa.Column("urgency_score", sa.Float(), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("created_from_context_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("delta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunities_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunities")),
    )
    op.create_index("ix_opportunities_company_created", "opportunities", ["company_id", "created_at"])
    op.create_index("ix_opportunities_recommendation", "opportunities", ["recommendation"])
    op.create_index("ix_opportunities_status_score", "opportunities", ["status", "opportunity_score"])

    op.create_table(
        "opportunity_scores",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score_name", sa.String(128), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_scores_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_scores_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_scores")),
    )
    op.create_index("ix_opportunity_scores_opportunity_name", "opportunity_scores", ["opportunity_id", "score_name"])

    op.create_table(
        "opportunity_evidence",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("polarity", sa.String(32), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_evidence_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_evidence_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_evidence")),
    )
    op.create_index("ix_opportunity_evidence_opportunity_type", "opportunity_evidence", ["opportunity_id", "source_type"])

    op.create_table(
        "opportunity_history",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_history_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_history_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_history")),
    )
    op.create_index("ix_opportunity_history_opportunity_action", "opportunity_history", ["opportunity_id", "action"])

    op.create_table(
        "opportunity_recommendations",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("next_step", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_recommendations_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_recommendations_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_recommendations")),
    )
    op.create_index("ix_opportunity_recommendations_opportunity_action", "opportunity_recommendations", ["opportunity_id", "action"])

    op.create_table(
        "opportunity_timeline",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_timeline_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_timeline_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_timeline")),
    )
    op.create_index("ix_opportunity_timeline_opportunity_created", "opportunity_timeline", ["opportunity_id", "created_at"])

    op.create_table(
        "opportunity_feedback",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=False),
        sa.Column("review_outcome", sa.String(64), nullable=False),
        sa.Column("corrected_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("outcome_label", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_feedback_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_feedback")),
    )
    op.create_index("ix_opportunity_feedback_opportunity_outcome", "opportunity_feedback", ["opportunity_id", "review_outcome"])

    op.create_table(
        "opportunity_conflicts",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conflict_type", sa.String(128), nullable=False),
        sa.Column("supporting_signal", sa.String(128), nullable=False),
        sa.Column("contradicting_signal", sa.String(128), nullable=False),
        sa.Column("severity", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_conflicts_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_conflicts_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_conflicts")),
    )
    op.create_index("ix_opportunity_conflicts_opportunity_type", "opportunity_conflicts", ["opportunity_id", "conflict_type"])

    op.create_table(
        "opportunity_lifecycle",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(64), nullable=True),
        sa.Column("to_status", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("rule_key", sa.String(128), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_lifecycle_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_lifecycle_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_lifecycle")),
    )
    op.create_index("ix_opportunity_lifecycle_opportunity_state", "opportunity_lifecycle", ["opportunity_id", "to_status"])

    op.create_table(
        "opportunity_metrics",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_metrics_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_metrics")),
    )
    op.create_index("ix_opportunity_metrics_name_created", "opportunity_metrics", ["metric_name", "created_at"])


def downgrade() -> None:
    for table in [
        "opportunity_metrics",
        "opportunity_lifecycle",
        "opportunity_conflicts",
        "opportunity_feedback",
        "opportunity_timeline",
        "opportunity_recommendations",
        "opportunity_history",
        "opportunity_evidence",
        "opportunity_scores",
        "opportunities",
    ]:
        op.drop_table(table)
