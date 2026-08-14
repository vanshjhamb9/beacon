"""Create communication gateway, conversation, and QA tables.

Revision ID: 20260720_0015
Revises: 20260720_0014
Create Date: 2026-07-20 03:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0015"
down_revision: str | None = "20260720_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base() -> list[sa.Column[object]]:
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
        "oauth_connections",
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("account_email", sa.String(255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", _json(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth_connections")),
    )
    op.create_index("ix_oauth_connections_provider_status", "oauth_connections", ["provider", "status"])

    op.create_table(
        "provider_secrets",
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("secret_name", sa.String(128), nullable=False),
        sa.Column("secret_value_encrypted", sa.Text(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_secrets")),
        sa.UniqueConstraint("provider", "secret_name", name=op.f("uq_provider_secrets_provider_secret_name")),
    )

    op.create_table(
        "communication_messages",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("to_address", sa.Text(), nullable=True),
        sa.Column("from_address", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("thread_id", sa.String(255), nullable=True),
        sa.Column("conversation_id", sa.String(255), nullable=True),
        sa.Column("sandbox", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attachments", _json(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_communication_messages_company_id_companies")),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name=op.f("fk_communication_messages_opportunity_id_opportunities")),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_communication_messages_campaign_id_campaigns")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_communication_messages")),
    )
    op.create_index("ix_communication_messages_campaign_state", "communication_messages", ["campaign_id", "state"])
    op.create_index("ix_communication_messages_thread", "communication_messages", ["thread_id"])

    op.create_table(
        "delivery_events",
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        *_base(),
        sa.ForeignKeyConstraint(["message_id"], ["communication_messages.id"], name=op.f("fk_delivery_events_message_id_communication_messages")),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_delivery_events_campaign_id_campaigns")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_events")),
    )
    op.create_index("ix_delivery_events_campaign_occurred", "delivery_events", ["campaign_id", "occurred_at"])

    op.create_table(
        "webhook_events",
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_base(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_events")),
    )
    op.create_index("ix_webhook_events_provider_created", "webhook_events", ["provider", "created_at"])

    op.create_table(
        "communication_queue_items",
        sa.Column("queue_name", sa.String(64), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        *_base(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_communication_queue_items")),
    )
    op.create_index("ix_communication_queue_items_queue_available", "communication_queue_items", ["queue_name", "available_at"])

    op.create_table(
        "conversation_threads",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("participants", _json(), nullable=False),
        sa.Column("channels", _json(), nullable=False),
        sa.Column("unread_count", sa.Integer(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        *_base(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_conversation_threads_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_threads")),
    )
    op.create_index("ix_conversation_threads_company_activity", "conversation_threads", ["company_id", "last_activity_at"])

    op.create_table(
        "conversation_items",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("item_type", sa.String(32), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("from_address", sa.Text(), nullable=True),
        sa.Column("to_address", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("thread_id", sa.String(255), nullable=True),
        sa.Column("attachments", _json(), nullable=False),
        sa.Column("unread", sa.Boolean(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        *_base(),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation_threads.id"], name=op.f("fk_conversation_items_conversation_id_conversation_threads")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_conversation_items_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_items")),
    )
    op.create_index("ix_conversation_items_conversation_occurred", "conversation_items", ["conversation_id", "occurred_at"])

    op.create_table(
        "sandbox_scenarios",
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("steps", _json(), nullable=False),
        sa.Column("result", _json(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        *_base(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sandbox_scenarios")),
    )

    op.create_table(
        "qa_health_snapshots",
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("components", _json(), nullable=False),
        sa.Column("recommendations", _json(), nullable=False),
        *_base(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qa_health_snapshots")),
    )
    op.create_index("ix_qa_health_snapshots_created", "qa_health_snapshots", ["created_at"])

    op.create_table(
        "campaign_stop_events",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_campaign_stop_events_campaign_id_campaigns")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_stop_events")),
    )


def downgrade() -> None:
    op.drop_table("campaign_stop_events")
    op.drop_index("ix_qa_health_snapshots_created", table_name="qa_health_snapshots")
    op.drop_table("qa_health_snapshots")
    op.drop_table("sandbox_scenarios")
    op.drop_index("ix_conversation_items_conversation_occurred", table_name="conversation_items")
    op.drop_table("conversation_items")
    op.drop_index("ix_conversation_threads_company_activity", table_name="conversation_threads")
    op.drop_table("conversation_threads")
    op.drop_index("ix_communication_queue_items_queue_available", table_name="communication_queue_items")
    op.drop_table("communication_queue_items")
    op.drop_index("ix_webhook_events_provider_created", table_name="webhook_events")
    op.drop_table("webhook_events")
    op.drop_index("ix_delivery_events_campaign_occurred", table_name="delivery_events")
    op.drop_table("delivery_events")
    op.drop_index("ix_communication_messages_thread", table_name="communication_messages")
    op.drop_index("ix_communication_messages_campaign_state", table_name="communication_messages")
    op.drop_table("communication_messages")
    op.drop_table("provider_secrets")
    op.drop_index("ix_oauth_connections_provider_status", table_name="oauth_connections")
    op.drop_table("oauth_connections")
