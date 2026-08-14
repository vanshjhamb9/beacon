"""Create Lead Intelligence Explorer (LIX v1) append-only tables.

Sprint brief referenced revision 20260727_0049. BIC already used 20260726_0049;
this revision id is 20260727_0049 with down_revision 20260726_0049.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260727_0049"
down_revision = "20260726_0049"
branch_labels = None
depends_on = None


def _base():
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "lead_events",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("stage", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("headline", sa.Text(), nullable=False, server_default=""),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("connector", sa.String(64), nullable=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_events_company_id", "lead_events", ["company_id"])
    op.create_index("ix_lead_events_occurred_at", "lead_events", ["occurred_at"])
    op.create_index("ix_lead_events_dedupe_key", "lead_events", ["dedupe_key"], unique=True)
    op.create_index("ix_lead_events_company_occurred", "lead_events", ["company_id", "occurred_at"])

    op.create_table(
        "lead_stage_history",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="passed"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("filters_passed", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("filters_failed", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_stage_history_company_id", "lead_stage_history", ["company_id"])
    op.create_index("ix_lead_stage_history_company_stage", "lead_stage_history", ["company_id", "stage"])
    op.create_index("ix_lead_stage_history_dedupe_key", "lead_stage_history", ["dedupe_key"], unique=True)

    op.create_table(
        "lead_provider_history",
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("fields_added", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("credits_used", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("revenue_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_provider_history_provider", "lead_provider_history", ["provider"])
    op.create_index("ix_lead_provider_history_company_id", "lead_provider_history", ["company_id"])
    op.create_index("ix_lead_provider_history_dedupe_key", "lead_provider_history", ["dedupe_key"], unique=True)

    op.create_table(
        "lead_score_breakdown",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("component_key", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("points", sa.Float(), nullable=False, server_default="0"),
        sa.Column("present", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("evidence", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_score_breakdown_company_id", "lead_score_breakdown", ["company_id"])
    op.create_index("ix_lead_score_breakdown_dedupe_key", "lead_score_breakdown", ["dedupe_key"], unique=True)

    op.create_table(
        "lead_field_history",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("field_name", sa.String(128), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="internal"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("evidence_id", UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_field_history_company_id", "lead_field_history", ["company_id"])
    op.create_index(
        "ix_lead_field_history_company_field",
        "lead_field_history",
        ["company_id", "field_name"],
    )
    op.create_index("ix_lead_field_history_dedupe_key", "lead_field_history", ["dedupe_key"], unique=True)

    op.create_table(
        "lead_evidence_chain",
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("label", sa.String(255), nullable=False, server_default=""),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_lead_evidence_chain_company_id", "lead_evidence_chain", ["company_id"])
    op.create_index("ix_lead_evidence_chain_kind", "lead_evidence_chain", ["kind"])
    op.create_index("ix_lead_evidence_chain_dedupe_key", "lead_evidence_chain", ["dedupe_key"], unique=True)


def downgrade() -> None:
    op.drop_table("lead_evidence_chain")
    op.drop_table("lead_field_history")
    op.drop_table("lead_score_breakdown")
    op.drop_table("lead_provider_history")
    op.drop_table("lead_stage_history")
    op.drop_table("lead_events")
