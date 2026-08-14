"""Create quality engine tables.

Revision ID: 20260710_0003
Revises: 20260710_0002
Create Date: 2026-07-10 18:21:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0003"
down_revision: str | None = "20260710_0002"
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
        "quality_reports",
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("grade", sa.String(length=16), nullable=False),
        sa.Column("schema_score", sa.Float(), nullable=False),
        sa.Column("spam_score", sa.Float(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("entity_confidence_score", sa.Float(), nullable=False),
        sa.Column("duplicate_probability", sa.Float(), nullable=False),
        sa.Column("overall_quality_score", sa.Float(), nullable=False),
        sa.Column("processing_time_ms", sa.Float(), nullable=False),
        sa.Column("queue_time_ms", sa.Float(), nullable=True),
        sa.Column("reason_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], name=op.f("fk_quality_reports_raw_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_reports")),
    )
    op.create_index("ix_quality_reports_decision_created", "quality_reports", ["decision", "created_at"])
    op.create_index("ix_quality_reports_overall_quality", "quality_reports", ["overall_quality_score"])
    op.create_index("ix_quality_reports_raw_event_created", "quality_reports", ["raw_event_id", "created_at"])
    op.create_index("ix_quality_reports_source_created", "quality_reports", ["source", "created_at"])

    op.create_table(
        "quality_metrics",
        sa.Column("quality_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("reason_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["quality_report_id"], ["quality_reports.id"], name=op.f("fk_quality_metrics_quality_report_id_quality_reports")),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], name=op.f("fk_quality_metrics_raw_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_metrics")),
    )
    op.create_index("ix_quality_metrics_metric_name_created", "quality_metrics", ["metric_name", "created_at"])
    op.create_index("ix_quality_metrics_report_stage", "quality_metrics", ["quality_report_id", "stage"])

    op.create_table(
        "quality_rules",
        sa.Column("rule_key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_rules")),
    )
    op.create_index("ix_quality_rules_category_enabled", "quality_rules", ["category", "enabled"])
    op.create_index("ix_quality_rules_key_version", "quality_rules", ["rule_key", "version"])

    op.create_table(
        "source_statistics",
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signals_collected", sa.Integer(), nullable=False),
        sa.Column("signals_accepted", sa.Integer(), nullable=False),
        sa.Column("signals_rejected", sa.Integer(), nullable=False),
        sa.Column("spam_rate", sa.Float(), nullable=False),
        sa.Column("duplicate_rate", sa.Float(), nullable=False),
        sa.Column("average_quality", sa.Float(), nullable=False),
        sa.Column("average_confidence", sa.Float(), nullable=False),
        sa.Column("average_processing_time_ms", sa.Float(), nullable=False),
        sa.Column("collector_health", sa.String(length=32), nullable=False),
        sa.Column("historical_trend", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_statistics")),
    )
    op.create_index("ix_source_statistics_average_quality", "source_statistics", ["average_quality"])
    op.create_index("ix_source_statistics_source_window", "source_statistics", ["source", "window_start", "window_end"])

    op.create_table(
        "spam_patterns",
        sa.Column("pattern_hash", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("pattern_type", sa.String(length=64), nullable=False),
        sa.Column("pattern", sa.Text(), nullable=False),
        sa.Column("occurrences", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spam_patterns")),
    )
    op.create_index("ix_spam_patterns_pattern_hash", "spam_patterns", ["pattern_hash"])
    op.create_index("ix_spam_patterns_source_seen", "spam_patterns", ["source", "last_seen_at"])

    op.create_table(
        "quality_audit",
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["quality_report_id"], ["quality_reports.id"], name=op.f("fk_quality_audit_quality_report_id_quality_reports")),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], name=op.f("fk_quality_audit_raw_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_audit")),
    )
    op.create_index("ix_quality_audit_action", "quality_audit", ["action"])
    op.create_index("ix_quality_audit_raw_event_created", "quality_audit", ["raw_event_id", "created_at"])

    op.create_table(
        "quality_feedback",
        sa.Column("quality_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=False),
        sa.Column("review_outcome", sa.String(length=64), nullable=False),
        sa.Column("corrected_decision", sa.String(length=32), nullable=True),
        sa.Column("corrected_reason_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["quality_report_id"], ["quality_reports.id"], name=op.f("fk_quality_feedback_quality_report_id_quality_reports")),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], name=op.f("fk_quality_feedback_raw_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_feedback")),
    )
    op.create_index("ix_quality_feedback_event_outcome", "quality_feedback", ["raw_event_id", "review_outcome"])
    op.create_index("ix_quality_feedback_report_created", "quality_feedback", ["quality_report_id", "created_at"])


def downgrade() -> None:
    op.drop_table("quality_feedback")
    op.drop_table("quality_audit")
    op.drop_table("spam_patterns")
    op.drop_table("source_statistics")
    op.drop_table("quality_rules")
    op.drop_table("quality_metrics")
    op.drop_table("quality_reports")
