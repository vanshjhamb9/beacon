"""Create Discovery Quality Engine v2 tables — scores, grades, reports."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260729_0055"
down_revision = "20260729_0054"
branch_labels = None
depends_on = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "quality_scores",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grade", sa.String(8), nullable=False, server_default=""),
        sa.Column("decision", sa.String(32), nullable=False, server_default=""),
        sa.Column("components", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("weights_version", sa.String(32), nullable=False, server_default="v2.0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_scores_company_id", "quality_scores", ["company_id"])
    op.create_index("ix_quality_scores_grade_created", "quality_scores", ["grade", "created_at"])
    op.create_index("ix_quality_scores_decision_created", "quality_scores", ["decision", "created_at"])
    op.create_index("ix_quality_scores_score_created", "quality_scores", ["total_score", "created_at"])

    op.create_table(
        "quality_reports_v2",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("quality_score_id", UUID(as_uuid=True), nullable=True),
        sa.Column("quality_grade", sa.String(8), nullable=False, server_default=""),
        sa.Column("decision", sa.String(32), nullable=False, server_default=""),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("audit_trail", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("gates_passed", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("gates_failed", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rejection_reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_quality_reports_v2_company_id", "quality_reports_v2", ["company_id"])
    op.create_index("ix_quality_reports_v2_grade_created", "quality_reports_v2", ["quality_grade", "created_at"])
    op.create_index("ix_quality_reports_v2_decision_created", "quality_reports_v2", ["decision", "created_at"])

    op.create_table(
        "freshness_evaluations",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("signal_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signal_age_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default=""),
        sa.Column("thresholds", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base(),
    )
    op.create_index("ix_freshness_evaluations_company_id", "freshness_evaluations", ["company_id"])
    op.create_index("ix_freshness_evaluations_status_created", "freshness_evaluations", ["status", "created_at"])

    op.create_table(
        "buying_signal_evaluations",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False, server_default=""),
        sa.Column("valid_signals", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("not_valid_signals", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("borderline_signals", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base(),
    )
    op.create_index("ix_buying_signal_evaluations_company_id", "buying_signal_evaluations", ["company_id"])
    op.create_index("ix_buying_signal_evaluations_verdict_created", "buying_signal_evaluations", ["verdict", "created_at"])

    op.create_table(
        "score_audit_trail",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", UUID(as_uuid=True), nullable=True),
        sa.Column("gate", sa.String(64), nullable=False, server_default=""),
        sa.Column("decision", sa.String(32), nullable=False, server_default=""),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_score_audit_trail_company_id", "score_audit_trail", ["company_id"])
    op.create_index("ix_score_audit_trail_report_id", "score_audit_trail", ["report_id"])
    op.create_index("ix_score_audit_trail_gate_created", "score_audit_trail", ["gate", "created_at"])


def downgrade() -> None:
    op.drop_table("score_audit_trail")
    op.drop_table("buying_signal_evaluations")
    op.drop_table("freshness_evaluations")
    op.drop_table("quality_reports_v2")
    op.drop_table("quality_scores")
