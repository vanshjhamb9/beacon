"""Create context intelligence tables.

Revision ID: 20260710_0004
Revises: 20260710_0003
Create Date: 2026-07-10 18:49:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0004"
down_revision: str | None = "20260710_0003"
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
        "business_contexts",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("classified_signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_urgency", sa.String(32), nullable=False),
        sa.Column("buying_stage", sa.String(64), nullable=False),
        sa.Column("decision_stage", sa.String(64), nullable=False),
        sa.Column("growth_stage", sa.String(64), nullable=False),
        sa.Column("digital_maturity", sa.Float(), nullable=False),
        sa.Column("ai_readiness", sa.Float(), nullable=False),
        sa.Column("automation_readiness", sa.Float(), nullable=False),
        sa.Column("budget_probability", sa.Float(), nullable=False),
        sa.Column("technology_maturity", sa.Float(), nullable=False),
        sa.Column("expansion_probability", sa.Float(), nullable=False),
        sa.Column("operational_pressure", sa.Float(), nullable=False),
        sa.Column("customer_experience_pressure", sa.Float(), nullable=False),
        sa.Column("support_pressure", sa.Float(), nullable=False),
        sa.Column("engineering_pressure", sa.Float(), nullable=False),
        sa.Column("marketing_pressure", sa.Float(), nullable=False),
        sa.Column("sales_pressure", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("processing_time_ms", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_business_contexts_company_id_companies")),
        sa.ForeignKeyConstraint(["classified_signal_id"], ["classified_signals.id"], name=op.f("fk_business_contexts_classified_signal_id_classified_signals")),
        sa.ForeignKeyConstraint(["quality_report_id"], ["quality_reports.id"], name=op.f("fk_business_contexts_quality_report_id_quality_reports")),
        sa.ForeignKeyConstraint(["raw_event_id"], ["raw_events.id"], name=op.f("fk_business_contexts_raw_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business_contexts")),
    )
    op.create_index("ix_business_contexts_company_created", "business_contexts", ["company_id", "created_at"])
    op.create_index("ix_business_contexts_confidence", "business_contexts", ["confidence"])
    op.create_index("ix_business_contexts_signal", "business_contexts", ["classified_signal_id"])

    for table in ["business_pains", "business_goals", "business_triggers", "business_impacts"]:
        op.create_table(
            table,
            sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("category", sa.String(128), nullable=False),
            sa.Column("value", sa.String(255), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            *_base_columns(),
            sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f(f"fk_{table}_business_context_id_business_contexts")),
            sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f(f"fk_{table}_company_id_companies")),
            sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
        )
        op.create_index(f"ix_{table}_company_category", table, ["company_id", "category"])

    op.create_table(
        "decision_signals",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buying_stage", sa.String(64), nullable=False),
        sa.Column("decision_stage", sa.String(64), nullable=False),
        sa.Column("decision_maker_type", sa.String(128), nullable=False),
        sa.Column("implementation_complexity", sa.String(64), nullable=False),
        sa.Column("potential_budget_range", sa.String(64), nullable=False),
        sa.Column("implementation_urgency", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_decision_signals_business_context_id_business_contexts")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_decision_signals_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_signals")),
    )
    op.create_index("ix_decision_signals_company_stage", "decision_signals", ["company_id", "decision_stage"])

    op.create_table(
        "technology_signals",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technology", sa.String(128), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("maturity_score", sa.Float(), nullable=False),
        sa.Column("adoption_signal", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_technology_signals_business_context_id_business_contexts")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_technology_signals_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_technology_signals")),
    )
    op.create_index("ix_technology_signals_company_technology", "technology_signals", ["company_id", "technology"])

    op.create_table(
        "industry_profiles",
        sa.Column("industry", sa.String(128), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("maturity_benchmarks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("common_pains", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("technology_patterns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_industry_profiles")),
    )
    op.create_index("ix_industry_profiles_industry", "industry_profiles", ["industry"])

    op.create_table(
        "company_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("business_model", sa.String(128), nullable=False),
        sa.Column("company_stage", sa.String(64), nullable=False),
        sa.Column("growth_pattern", sa.String(128), nullable=False),
        sa.Column("technology_stack", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("digital_maturity", sa.Float(), nullable=False),
        sa.Column("ai_adoption", sa.Float(), nullable=False),
        sa.Column("automation_adoption", sa.Float(), nullable=False),
        sa.Column("hiring_pattern", sa.String(128), nullable=False),
        sa.Column("expansion_pattern", sa.String(128), nullable=False),
        sa.Column("innovation_score", sa.Float(), nullable=False),
        sa.Column("support_maturity", sa.Float(), nullable=False),
        sa.Column("operational_maturity", sa.Float(), nullable=False),
        sa.Column("technology_maturity", sa.Float(), nullable=False),
        sa.Column("customer_maturity", sa.Float(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_company_profiles_business_context_id_business_contexts")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_profiles_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_profiles")),
    )
    op.create_index("ix_company_profiles_company_created", "company_profiles", ["company_id", "created_at"])

    op.create_table(
        "context_history",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_context_history_business_context_id_business_contexts")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_context_history_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_context_history")),
    )
    op.create_index("ix_context_history_company_action", "context_history", ["company_id", "action"])

    op.create_table(
        "context_evidence",
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_key", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_context_evidence_business_context_id_business_contexts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_context_evidence")),
    )
    op.create_index("ix_context_evidence_context_type", "context_evidence", ["business_context_id", "evidence_type"])

    op.create_table(
        "context_feedback",
        sa.Column("business_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=False),
        sa.Column("review_outcome", sa.String(64), nullable=False),
        sa.Column("corrected_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ground_truth", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["business_context_id"], ["business_contexts.id"], name=op.f("fk_context_feedback_business_context_id_business_contexts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_context_feedback")),
    )
    op.create_index("ix_context_feedback_context_outcome", "context_feedback", ["business_context_id", "review_outcome"])


def downgrade() -> None:
    for table in [
        "context_feedback",
        "context_evidence",
        "context_history",
        "company_profiles",
        "industry_profiles",
        "technology_signals",
        "decision_signals",
        "business_impacts",
        "business_triggers",
        "business_goals",
        "business_pains",
        "business_contexts",
    ]:
        op.drop_table(table)
