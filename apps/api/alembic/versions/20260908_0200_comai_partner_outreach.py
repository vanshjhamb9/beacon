"""create comai partner outreach tables

Revision ID: 20260908_0200
Revises: 20260817_0101
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260908_0200"
down_revision = "20260817_0101"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comai_partner_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="validating"),
        sa.Column("kill_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("config_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("video_url", sa.String(1024), nullable=False, server_default=""),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("drafted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queued", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("row_errors", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_comai_partner_campaigns_status", "comai_partner_campaigns", ["status"])

    op.create_table(
        "comai_partner_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("campaign_id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, server_default=""),
        sa.Column("first_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("agency_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("agency_type", sa.String(128), nullable=False, server_default=""),
        sa.Column("website", sa.String(512), nullable=False, server_default=""),
        sa.Column("domain", sa.String(255), nullable=False, server_default=""),
        sa.Column("city", sa.String(128), nullable=False, server_default=""),
        sa.Column("phone", sa.String(64), nullable=False, server_default=""),
        sa.Column("services", sa.Text(), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("client_examples", sa.Text(), nullable=False, server_default=""),
        sa.Column("stage", sa.String(64), nullable=False, server_default="uploaded"),
        sa.Column("sequence_step", sa.String(32), nullable=False, server_default=""),
        sa.Column("next_followup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stop_reason", sa.String(128), nullable=False, server_default=""),
        sa.Column("subject", sa.String(512), nullable=False, server_default=""),
        sa.Column("body_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reply_class", sa.String(64), nullable=False, server_default=""),
        sa.Column("reply_snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("send_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("row_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_comai_partner_leads_campaign_id", "comai_partner_leads", ["campaign_id"])
    op.create_index("ix_comai_partner_leads_email", "comai_partner_leads", ["email"])
    op.create_index("ix_comai_partner_leads_stage", "comai_partner_leads", ["stage"])
    op.create_index("ix_comai_partner_leads_next_followup_at", "comai_partner_leads", ["next_followup_at"])

    op.create_table(
        "comai_partner_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("campaign_id", sa.String(36), nullable=False),
        sa.Column("lead_id", sa.String(36), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False, server_default="outbound"),
        sa.Column("step", sa.String(32), nullable=False, server_default="intro"),
        sa.Column("subject", sa.String(512), nullable=False, server_default=""),
        sa.Column("body_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.Column("delivery_state", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("provider_message_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("thread_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("reply_class", sa.String(64), nullable=False, server_default=""),
    )
    op.create_index("ix_comai_partner_messages_campaign_id", "comai_partner_messages", ["campaign_id"])
    op.create_index("ix_comai_partner_messages_lead_id", "comai_partner_messages", ["lead_id"])
    op.create_index("ix_comai_partner_messages_direction", "comai_partner_messages", ["direction"])

    op.create_table(
        "comai_partner_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("campaign_id", sa.String(36), nullable=False),
        sa.Column("lead_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False, server_default=""),
        sa.Column("detail", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_comai_partner_events_campaign_id", "comai_partner_events", ["campaign_id"])
    op.create_index("ix_comai_partner_events_event_type", "comai_partner_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("comai_partner_events")
    op.drop_table("comai_partner_messages")
    op.drop_table("comai_partner_leads")
    op.drop_table("comai_partner_campaigns")
