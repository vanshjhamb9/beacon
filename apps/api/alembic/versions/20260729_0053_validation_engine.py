"""Create Validation & Continuous Learning Platform append-only tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260729_0053"
down_revision = "20260729_0052"
branch_labels = None
depends_on = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "validation_events",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_validation_events_company_stage", "validation_events", ["company_id", "stage"])
    op.create_index("ix_validation_events_stage_created", "validation_events", ["stage", "created_at"])
    op.create_index("ix_validation_events_source_created", "validation_events", ["source", "created_at"])

    op.create_table(
        "lead_outcomes",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("service_sold", sa.String(255), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_outcomes_company_id", "lead_outcomes", ["company_id"])
    op.create_index("ix_lead_outcomes_status_created", "lead_outcomes", ["status", "created_at"])

    op.create_table(
        "reply_events",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("reply_type", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("reply_time_seconds", sa.Float(), nullable=True),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_reply_events_company_id", "reply_events", ["company_id"])
    op.create_index("ix_reply_events_reply_type_created", "reply_events", ["reply_type", "created_at"])
    op.create_index("ix_reply_events_source_created", "reply_events", ["source", "created_at"])

    op.create_table(
        "meeting_events",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("meeting_type", sa.String(64), nullable=False),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("calendar_link", sa.String(512), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("next_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_meeting_events_company_id", "meeting_events", ["company_id"])
    op.create_index("ix_meeting_events_meeting_type_created", "meeting_events", ["meeting_type", "created_at"])

    op.create_table(
        "proposal_events",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_proposal_events_company_id", "proposal_events", ["company_id"])
    op.create_index("ix_proposal_events_status_created", "proposal_events", ["status", "created_at"])

    op.create_table(
        "deal_events",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("service_sold", sa.String(255), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_deal_events_company_id", "deal_events", ["company_id"])
    op.create_index("ix_deal_events_status_created", "deal_events", ["status", "created_at"])

    op.create_table(
        "validation_timelines",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False, server_default=""),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_validation_timelines_company_stage", "validation_timelines", ["company_id", "stage"])
    op.create_index("ix_validation_timelines_company_created", "validation_timelines", ["company_id", "created_at"])

    op.create_table(
        "connector_roi",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_connector_roi_connector", "connector_roi", ["connector"], unique=True)

    op.create_table(
        "service_roi",
        sa.Column("service", sa.String(255), nullable=False),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("proposal_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_service_roi_service", "service_roi", ["service"], unique=True)

    op.create_table(
        "industry_roi",
        sa.Column("industry", sa.String(128), nullable=False),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_industry_roi_industry", "industry_roi", ["industry"], unique=True)

    op.create_table(
        "persona_roi",
        sa.Column("persona", sa.String(128), nullable=False),
        sa.Column("contacted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_persona_roi_persona", "persona_roi", ["persona"], unique=True)

    op.create_table(
        "trigger_roi",
        sa.Column("trigger", sa.String(64), nullable=False),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_trigger_roi_trigger", "trigger_roi", ["trigger"], unique=True)

    op.create_table(
        "objection_events",
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("industry", sa.String(128), nullable=False, server_default=""),
        sa.Column("service", sa.String(255), nullable=False, server_default=""),
        sa.Column("connector", sa.String(64), nullable=False, server_default=""),
        sa.Column("persona", sa.String(128), nullable=False, server_default=""),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_objection_events_company_id", "objection_events", ["company_id"])
    op.create_index("ix_objection_events_category_created", "objection_events", ["category", "created_at"])
    op.create_index("ix_objection_events_industry_created", "objection_events", ["industry", "created_at"])
    op.create_index("ix_objection_events_service_created", "objection_events", ["service", "created_at"])

    op.create_table(
        "validation_snapshots",
        sa.Column("total_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_deal_size", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("proposal_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_lost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_meetings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_proposals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_validation_snapshots_created_at", "validation_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_table("validation_snapshots")
    op.drop_table("objection_events")
    op.drop_table("trigger_roi")
    op.drop_table("persona_roi")
    op.drop_table("industry_roi")
    op.drop_table("service_roi")
    op.drop_table("connector_roi")
    op.drop_table("validation_timelines")
    op.drop_table("deal_events")
    op.drop_table("proposal_events")
    op.drop_table("meeting_events")
    op.drop_table("reply_events")
    op.drop_table("lead_outcomes")
    op.drop_table("validation_events")
