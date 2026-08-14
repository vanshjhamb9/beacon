"""Create intelligence improvement tables.

Revision ID: 20260710_0006
Revises: 20260710_0005
Create Date: 2026-07-10 19:31:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0006"
down_revision: str | None = "20260710_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column[object]]:
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
        "learning_events",
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("area", sa.String(64), nullable=False),
        sa.Column("entity_key", sa.String(255), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_events")),
    )
    op.create_index("ix_learning_events_area_created", "learning_events", ["area", "created_at"])

    op.create_table(
        "feedback_events",
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("area", sa.String(64), nullable=False),
        sa.Column("entity_key", sa.String(255), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback_events")),
    )
    op.create_index("ix_feedback_events_source_area", "feedback_events", ["source", "area"])

    op.create_table(
        "ground_truth",
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("value", _json(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ground_truth")),
    )
    op.create_index("ix_ground_truth_entity", "ground_truth", ["entity_type", "entity_id"])

    op.create_table(
        "collector_performance",
        sa.Column("collector", sa.String(128), nullable=False),
        sa.Column("precision", sa.Float(), nullable=False),
        sa.Column("recall", sa.Float(), nullable=False),
        sa.Column("spam_rate", sa.Float(), nullable=False),
        sa.Column("duplicate_rate", sa.Float(), nullable=False),
        sa.Column("conversion_rate", sa.Float(), nullable=False),
        sa.Column("average_quality", sa.Float(), nullable=False),
        sa.Column("average_confidence", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("ranking", sa.Integer(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collector_performance")),
    )
    op.create_index("ix_collector_performance_collector_created", "collector_performance", ["collector", "created_at"])

    op.create_table(
        "quality_rule_performance",
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("times_fired", sa.Integer(), nullable=False),
        sa.Column("correct_decisions", sa.Integer(), nullable=False),
        sa.Column("incorrect_decisions", sa.Integer(), nullable=False),
        sa.Column("override_rate", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("historical_trend", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_rule_performance")),
    )
    op.create_index("ix_quality_rule_performance_rule_created", "quality_rule_performance", ["rule_key", "created_at"])

    op.create_table(
        "classifier_performance",
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("times_fired", sa.Integer(), nullable=False),
        sa.Column("correct_decisions", sa.Integer(), nullable=False),
        sa.Column("incorrect_decisions", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("historical_trend", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classifier_performance")),
    )
    op.create_index("ix_classifier_performance_rule_created", "classifier_performance", ["rule_key", "created_at"])

    op.create_table(
        "context_accuracy",
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=False),
        sa.Column("corrected_fields", _json(), nullable=False),
        sa.Column("ground_truth", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_context_accuracy_business_context_id_business_contexts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_context_accuracy")),
    )
    op.create_index("ix_context_accuracy_context_created", "context_accuracy", ["business_context_id", "created_at"])

    op.create_table(
        "opportunity_accuracy",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("predicted_score", sa.Float(), nullable=False),
        sa.Column("actual_outcome_score", sa.Float(), nullable=False),
        sa.Column("prediction_error", sa.Float(), nullable=False),
        sa.Column("outcome_label", sa.String(128), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_accuracy_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_accuracy")),
    )
    op.create_index("ix_opportunity_accuracy_opportunity_created", "opportunity_accuracy", ["opportunity_id", "created_at"])

    op.create_table(
        "recommendation_accuracy",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommended_action", sa.String(128), nullable=False),
        sa.Column("actual_outcome", sa.String(128), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_recommendation_accuracy_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recommendation_accuracy")),
    )
    op.create_index("ix_recommendation_accuracy_action_created", "recommendation_accuracy", ["recommended_action", "created_at"])

    op.create_table(
        "prediction_history",
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediction_type", sa.String(128), nullable=False),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("error", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(128), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prediction_history")),
    )
    op.create_index("ix_prediction_history_entity_created", "prediction_history", ["entity_type", "entity_id", "created_at"])

    op.create_table(
        "conversion_outcomes",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(128), nullable=False),
        sa.Column("outcome_value", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_conversion_outcomes_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_conversion_outcomes_opportunity_id_opportunities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversion_outcomes")),
    )
    op.create_index("ix_conversion_outcomes_opportunity_outcome", "conversion_outcomes", ["opportunity_id", "outcome"])

    op.create_table(
        "weight_adjustments",
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_key", sa.String(255), nullable=False),
        sa.Column("current_weight", sa.Float(), nullable=True),
        sa.Column("recommended_weight", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_approval", sa.String(8), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weight_adjustments")),
    )
    op.create_index("ix_weight_adjustments_target_created", "weight_adjustments", ["target_key", "created_at"])

    op.create_table(
        "experiment_runs",
        sa.Column("experiment_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("area", sa.String(64), nullable=False),
        sa.Column("variant_a", _json(), nullable=False),
        sa.Column("variant_b", _json(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiment_runs")),
    )
    op.create_index("ix_experiment_runs_key_created", "experiment_runs", ["experiment_key", "created_at"])

    op.create_table(
        "experiment_results",
        sa.Column("experiment_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant", sa.String(64), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["experiment_run_id"], ["experiment_runs.id"], name=op.f("fk_experiment_results_experiment_run_id_experiment_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiment_results")),
    )
    op.create_index("ix_experiment_results_run_variant", "experiment_results", ["experiment_run_id", "variant"])

    for table, key_column in [("model_versions", "model_key"), ("rule_versions", "rule_key")]:
        op.create_table(
            table,
            sa.Column(key_column, sa.String(128), nullable=False),
            sa.Column("version", sa.String(64), nullable=False),
            sa.Column("area", sa.String(64), nullable=False),
            sa.Column("parameters", _json(), nullable=False),
            sa.Column("status", sa.String(64), nullable=False),
            *_base_columns(),
            sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
        )
        op.create_index(f"ix_{table}_{key_column}_version", table, [key_column, "version"])


def downgrade() -> None:
    for table in [
        "rule_versions",
        "model_versions",
        "experiment_results",
        "experiment_runs",
        "weight_adjustments",
        "conversion_outcomes",
        "prediction_history",
        "recommendation_accuracy",
        "opportunity_accuracy",
        "context_accuracy",
        "classifier_performance",
        "quality_rule_performance",
        "collector_performance",
        "ground_truth",
        "feedback_events",
        "learning_events",
    ]:
        op.drop_table(table)
