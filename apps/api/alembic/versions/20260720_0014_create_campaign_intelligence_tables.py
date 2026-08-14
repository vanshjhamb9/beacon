"""Create campaign intelligence tables.

Revision ID: 20260720_0014
Revises: 20260720_0013
Create Date: 2026-07-20 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0014"
down_revision: str | None = "20260720_0013"
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
        "campaign_templates",
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(64), nullable=False),
        sa.Column("style", sa.String(64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", _json(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_templates")),
    )
    op.create_index("ix_campaign_templates_channel_style", "campaign_templates", ["channel", "style"])

    op.create_table(
        "campaign_channels",
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("supports_async", sa.Boolean(), nullable=False),
        sa.Column("supports_attachments", sa.Boolean(), nullable=False),
        sa.Column("requires_opt_in", sa.Boolean(), nullable=False),
        sa.Column("max_daily_sends", sa.Integer(), nullable=False),
        sa.Column("min_gap_hours", sa.Float(), nullable=False),
        sa.Column("business_hours_only", sa.Boolean(), nullable=False),
        sa.Column("constraints", _json(), nullable=False),
        sa.Column("delivery_ready", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_channels")),
        sa.UniqueConstraint("kind", name=op.f("uq_campaign_channels_kind")),
    )

    op.create_table(
        "campaigns",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sales_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(32), nullable=False),
        sa.Column("primary_channel", sa.String(64), nullable=False),
        sa.Column("secondary_channel", sa.String(64), nullable=True),
        sa.Column("follow_up_count", sa.Integer(), nullable=False),
        sa.Column("delay_hours_between_messages", _json(), nullable=False),
        sa.Column("expected_confidence", sa.Float(), nullable=False),
        sa.Column("channel_choice_reason", sa.Text(), nullable=False),
        sa.Column("timing_reason", sa.Text(), nullable=False),
        sa.Column("message_selection_reason", sa.Text(), nullable=False),
        sa.Column("recommended_service", sa.String(255), nullable=False),
        sa.Column("business_pain", sa.Text(), nullable=False),
        sa.Column("buyer_persona", sa.String(128), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("communication_style", sa.String(64), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("schedule_rules", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("quality", _json(), nullable=False),
        sa.Column("plan_payload", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_campaigns_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_campaigns_opportunity_id_opportunities")),
        sa.ForeignKeyConstraint(["sales_package_id"], ["sales_packages.id"], name=op.f("fk_campaigns_sales_package_id_sales_packages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaigns")),
    )
    op.create_index("ix_campaigns_company_created", "campaigns", ["company_id", "created_at"])
    op.create_index("ix_campaigns_status_priority", "campaigns", ["status", "priority"])
    op.create_index("ix_campaigns_opportunity_created", "campaigns", ["opportunity_id", "created_at"])

    op.create_table(
        "campaign_steps",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(64), nullable=False),
        sa.Column("delay_hours", sa.Float(), nullable=False),
        sa.Column("draft_kind", sa.String(64), nullable=False),
        sa.Column("draft_style", sa.String(64), nullable=False),
        sa.Column("subject_preview", sa.Text(), nullable=False),
        sa.Column("body_preview", sa.Text(), nullable=False),
        sa.Column("message_selection_reason", sa.Text(), nullable=False),
        sa.Column("timing_reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("sales_draft_ref", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_campaign_steps_campaign_id_campaigns")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_campaign_steps_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_steps")),
    )
    op.create_index("ix_campaign_steps_campaign_sequence", "campaign_steps", ["campaign_id", "sequence"])

    op.create_table(
        "campaign_schedules",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("rules_snapshot", _json(), nullable=False),
        sa.Column("timing_reason", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_campaign_schedules_campaign_id_campaigns")),
        sa.ForeignKeyConstraint(["campaign_step_id"], ["campaign_steps.id"], name=op.f("fk_campaign_schedules_campaign_step_id_campaign_steps")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_campaign_schedules_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_schedules")),
    )
    op.create_index("ix_campaign_schedules_planned", "campaign_schedules", ["planned_at", "status"])
    op.create_index("ix_campaign_schedules_campaign", "campaign_schedules", ["campaign_id", "planned_at"])

    op.create_table(
        "campaign_approvals",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=False),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_campaign_approvals_campaign_id_campaigns")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_campaign_approvals_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_approvals")),
    )
    op.create_index("ix_campaign_approvals_campaign_created", "campaign_approvals", ["campaign_id", "created_at"])

    op.create_table(
        "campaign_execution_logs",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("delivery_attempted", sa.Boolean(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_campaign_execution_logs_campaign_id_campaigns")),
        sa.ForeignKeyConstraint(["campaign_step_id"], ["campaign_steps.id"], name=op.f("fk_campaign_execution_logs_campaign_step_id_campaign_steps")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_campaign_execution_logs_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_execution_logs")),
    )
    op.create_index("ix_campaign_execution_logs_campaign_created", "campaign_execution_logs", ["campaign_id", "created_at"])

    op.create_table(
        "campaign_audit",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("before_state", _json(), nullable=False),
        sa.Column("after_state", _json(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_campaign_audit_campaign_id_campaigns")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_campaign_audit_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_audit")),
    )
    op.create_index("ix_campaign_audit_campaign_created", "campaign_audit", ["campaign_id", "created_at"])
    op.create_index("ix_campaign_audit_company_created", "campaign_audit", ["company_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_campaign_audit_company_created", table_name="campaign_audit")
    op.drop_index("ix_campaign_audit_campaign_created", table_name="campaign_audit")
    op.drop_table("campaign_audit")
    op.drop_index("ix_campaign_execution_logs_campaign_created", table_name="campaign_execution_logs")
    op.drop_table("campaign_execution_logs")
    op.drop_index("ix_campaign_approvals_campaign_created", table_name="campaign_approvals")
    op.drop_table("campaign_approvals")
    op.drop_index("ix_campaign_schedules_campaign", table_name="campaign_schedules")
    op.drop_index("ix_campaign_schedules_planned", table_name="campaign_schedules")
    op.drop_table("campaign_schedules")
    op.drop_index("ix_campaign_steps_campaign_sequence", table_name="campaign_steps")
    op.drop_table("campaign_steps")
    op.drop_index("ix_campaigns_opportunity_created", table_name="campaigns")
    op.drop_index("ix_campaigns_status_priority", table_name="campaigns")
    op.drop_index("ix_campaigns_company_created", table_name="campaigns")
    op.drop_table("campaigns")
    op.drop_table("campaign_channels")
    op.drop_index("ix_campaign_templates_channel_style", table_name="campaign_templates")
    op.drop_table("campaign_templates")
