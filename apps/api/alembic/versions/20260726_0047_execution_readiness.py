"""Create Communication Readiness Gate / execution readiness tables (er-v1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260726_0047"
down_revision = "20260725_0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "communication_provider_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(64), nullable=False, server_default="00000000-0000-4000-8000-000000000001"),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("oauth_valid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("webhook_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_send", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_receive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_communication_provider_status_org_provider",
        "communication_provider_status",
        ["organization_id", "provider"],
        unique=False,
    )

    op.create_table(
        "execution_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(64), nullable=False, server_default="00000000-0000-4000-8000-000000000001"),
        sa.Column("execution_mode", sa.String(32), nullable=False, server_default="PLANNING"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("communication_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("whatsapp_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tracking_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("followup_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_execution_status_organization_id", "execution_status", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_table("execution_status")
    op.drop_table("communication_provider_status")
