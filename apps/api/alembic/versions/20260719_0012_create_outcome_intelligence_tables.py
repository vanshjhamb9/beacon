"""Create outcome intelligence tables.

Revision ID: 20260719_0012
Revises: 20260719_0011
Create Date: 2026-07-19 04:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0012"
down_revision: str | None = "20260719_0011"
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
        "opportunity_outcomes",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lifecycle_stage", sa.String(64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proposal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("recommended_service", sa.String(255), nullable=True),
        sa.Column("buyer_persona", sa.String(128), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("collector", sa.String(64), nullable=True),
        sa.Column("technology", sa.String(128), nullable=True),
        sa.Column("decision_maker_role", sa.String(128), nullable=True),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_opportunity_outcomes_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_opportunity_outcomes_opportunity_id_opportunities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_outcomes")),
        sa.UniqueConstraint("opportunity_id", name=op.f("uq_opportunity_outcomes_opportunity_id")),
    )
    op.create_index("ix_opportunity_outcomes_opportunity_stage", "opportunity_outcomes", ["opportunity_id", "lifecycle_stage"])
    op.create_index("ix_opportunity_outcomes_company_updated", "opportunity_outcomes", ["company_id", "updated_at"])

    op.create_table(
        "contact_attempts",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(64), nullable=False),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("replied", sa.Boolean(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_contact_attempts_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_contact_attempts_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["outcome_id"], ["opportunity_outcomes.id"], name=op.f("fk_contact_attempts_outcome_id_opportunity_outcomes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contact_attempts")),
    )
    op.create_index("ix_contact_attempts_opportunity_created", "contact_attempts", ["opportunity_id", "created_at"])

    op.create_table(
        "meetings",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meeting_type", sa.String(64), nullable=True),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_meetings_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_meetings_opportunity_id_opportunities")),
        sa.ForeignKeyConstraint(["outcome_id"], ["opportunity_outcomes.id"], name=op.f("fk_meetings_outcome_id_opportunity_outcomes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meetings")),
    )
    op.create_index("ix_meetings_opportunity_scheduled", "meetings", ["opportunity_id", "scheduled_at"])

    op.create_table(
        "proposals",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_proposals_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_proposals_opportunity_id_opportunities")),
        sa.ForeignKeyConstraint(["outcome_id"], ["opportunity_outcomes.id"], name=op.f("fk_proposals_outcome_id_opportunity_outcomes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_proposals")),
    )
    op.create_index("ix_proposals_opportunity_sent", "proposals", ["opportunity_id", "sent_at"])

    op.create_table(
        "deals",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_deals_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_deals_opportunity_id_opportunities")),
        sa.ForeignKeyConstraint(["outcome_id"], ["opportunity_outcomes.id"], name=op.f("fk_deals_outcome_id_opportunity_outcomes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deals")),
    )
    op.create_index("ix_deals_opportunity_closed", "deals", ["opportunity_id", "closed_at"])

    op.create_table(
        "customer_feedback",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(128), nullable=True),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_customer_feedback_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_customer_feedback_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["outcome_id"], ["opportunity_outcomes.id"], name=op.f("fk_customer_feedback_outcome_id_opportunity_outcomes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_feedback")),
    )
    op.create_index("ix_customer_feedback_company_created", "customer_feedback", ["company_id", "created_at"])

    for table, key_col, index_name in (
        ("prediction_accuracy", "metric_key", "ix_prediction_accuracy_key_created"),
        ("service_accuracy", "service_key", "ix_service_accuracy_service_created"),
        ("collector_accuracy", "collector", "ix_collector_accuracy_collector_created"),
        ("persona_accuracy", "persona", "ix_persona_accuracy_persona_created"),
        ("industry_accuracy", "industry", "ix_industry_accuracy_industry_created"),
    ):
        op.create_table(
            table,
            sa.Column(key_col, sa.String(255 if "service" in table else 128), nullable=False),
            sa.Column("sample_size", sa.Integer(), nullable=False),
            sa.Column("accuracy_score", sa.Float(), nullable=False),
            sa.Column("precision", sa.Float(), nullable=False),
            sa.Column("recall", sa.Float(), nullable=False),
            sa.Column("average_prediction_error", sa.Float(), nullable=False),
            sa.Column("details", _json(), nullable=False),
            *_base_columns(),
            sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
        )
        op.create_index(index_name, table, [key_col, "created_at"])

    op.create_table(
        "learning_metrics",
        sa.Column("area", sa.String(64), nullable=False),
        sa.Column("target_key", sa.String(255), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_metrics")),
    )
    op.create_index("ix_learning_metrics_area_created", "learning_metrics", ["area", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_learning_metrics_area_created", table_name="learning_metrics")
    op.drop_table("learning_metrics")
    for table, index_name in (
        ("industry_accuracy", "ix_industry_accuracy_industry_created"),
        ("persona_accuracy", "ix_persona_accuracy_persona_created"),
        ("collector_accuracy", "ix_collector_accuracy_collector_created"),
        ("service_accuracy", "ix_service_accuracy_service_created"),
        ("prediction_accuracy", "ix_prediction_accuracy_key_created"),
    ):
        op.drop_index(index_name, table_name=table)
        op.drop_table(table)
    op.drop_index("ix_customer_feedback_company_created", table_name="customer_feedback")
    op.drop_table("customer_feedback")
    op.drop_index("ix_deals_opportunity_closed", table_name="deals")
    op.drop_table("deals")
    op.drop_index("ix_proposals_opportunity_sent", table_name="proposals")
    op.drop_table("proposals")
    op.drop_index("ix_meetings_opportunity_scheduled", table_name="meetings")
    op.drop_table("meetings")
    op.drop_index("ix_contact_attempts_opportunity_created", table_name="contact_attempts")
    op.drop_table("contact_attempts")
    op.drop_index("ix_opportunity_outcomes_company_updated", table_name="opportunity_outcomes")
    op.drop_index("ix_opportunity_outcomes_opportunity_stage", table_name="opportunity_outcomes")
    op.drop_table("opportunity_outcomes")
