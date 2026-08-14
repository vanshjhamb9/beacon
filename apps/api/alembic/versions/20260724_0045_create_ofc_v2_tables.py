"""Create Operation First Customer (OFC v2) outreach tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0045"
down_revision = "20260724_0044"
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
        "ofc_outreach_records",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="READY"),
        sa.Column("status_history", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("brief", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pipeline_value", sa.Float(), nullable=False, server_default="5000"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="ofc-v2"),
        *_base(),
    )
    op.create_index("ix_ofc_outreach_records_company_id", "ofc_outreach_records", ["company_id"], unique=False)
    op.create_index("ix_ofc_outreach_records_status", "ofc_outreach_records", ["status"])

    op.create_table(
        "ofc_timeline_events",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_ofc_timeline_events_record_id", "ofc_timeline_events", ["record_id"])

    op.create_table(
        "ofc_founder_notes",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_ofc_founder_notes_record_id", "ofc_founder_notes", ["record_id"])

    op.create_table(
        "ofc_objection_events",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_ofc_objection_events_record_id", "ofc_objection_events", ["record_id"])
    op.create_index("ix_ofc_objection_events_label", "ofc_objection_events", ["label"])

    op.create_table(
        "ofc_daily_reports",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("today_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("vansh_ready_answer", sa.String(8), nullable=False, server_default="NO"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="ofc-v2"),
        *_base(),
    )


def downgrade() -> None:
    op.drop_table("ofc_daily_reports")
    op.drop_table("ofc_objection_events")
    op.drop_table("ofc_founder_notes")
    op.drop_table("ofc_timeline_events")
    op.drop_table("ofc_outreach_records")
