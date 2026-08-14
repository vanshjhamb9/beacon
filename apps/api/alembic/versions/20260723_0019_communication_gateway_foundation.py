"""Sprint 18A communication gateway foundation indexes.

Revision ID: 20260723_0019
Revises: 20260723_0018
Create Date: 2026-07-23 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0019"
down_revision: str | None = "20260723_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_communication_messages_provider_message_id",
        "communication_messages",
        ["provider_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_communication_messages_campaign_step",
        "communication_messages",
        ["campaign_id", "campaign_step_id"],
        unique=False,
    )
    # Optional history cursor lives in oauth_connections.metadata_json (no column needed).
    op.add_column(
        "communication_queue_items",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_communication_queue_items_idempotency",
        "communication_queue_items",
        ["idempotency_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_communication_queue_items_idempotency", table_name="communication_queue_items")
    op.drop_column("communication_queue_items", "idempotency_key")
    op.drop_index("ix_communication_messages_campaign_step", table_name="communication_messages")
    op.drop_index("ix_communication_messages_provider_message_id", table_name="communication_messages")
