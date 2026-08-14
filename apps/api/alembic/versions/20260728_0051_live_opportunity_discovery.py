"""Create Live Opportunity Discovery Engine append-only tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260728_0051"
down_revision = "20260728_0050"
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
        "live_opportunity_events",
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("normalized_company", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("buying_event", sa.String(255), nullable=False),
        sa.Column("service_match", sa.String(255), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_age_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("source_quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("buying_intent_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("company_size_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("funding_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_maker_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("revenue_potential_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("competition_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("service_match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("priority_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="P3"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("why_now", sa.Text(), nullable=False, server_default=""),
        sa.Column("why_today", sa.Text(), nullable=False, server_default=""),
        sa.Column("best_service", sa.String(255), nullable=False, server_default=""),
        sa.Column("revenue", sa.String(128), nullable=True),
        sa.Column("decision_maker", sa.String(255), nullable=True),
        sa.Column("dedupe_key", sa.String(191), nullable=False),
        sa.Column("score_breakdown", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reasons", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_live_opportunity_events_company", "live_opportunity_events", ["normalized_company"])
    op.create_index("ix_live_opportunity_events_category", "live_opportunity_events", ["category"])
    op.create_index("ix_live_opportunity_events_timestamp", "live_opportunity_events", ["event_timestamp"])
    op.create_index("ix_live_opportunity_events_priority", "live_opportunity_events", ["priority_score"])
    op.create_index("ix_live_opportunity_events_dedupe", "live_opportunity_events", ["dedupe_key"])

    op.create_table(
        "live_opportunity_evidence",
        sa.Column("event_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("headline", sa.String(512), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["live_opportunity_events.id"],
            name=op.f("fk_live_opportunity_evidence_event_id_live_opportunity_events"),
        ),
    )
    op.create_index("ix_live_opportunity_evidence_event", "live_opportunity_evidence", ["event_id"])
    op.create_index("ix_live_opportunity_evidence_source", "live_opportunity_evidence", ["source"])


def downgrade() -> None:
    op.drop_table("live_opportunity_evidence")
    op.drop_table("live_opportunity_events")
