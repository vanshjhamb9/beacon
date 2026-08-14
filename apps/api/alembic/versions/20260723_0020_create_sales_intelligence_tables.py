"""Create sales intelligence append-only tables.

Revision ID: 20260723_0020
Revises: 20260723_0019
Create Date: 2026-07-23 19:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0020"
down_revision: str | None = "20260723_0019"
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
        "sales_intelligence_snapshots",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("buying_intent_score", sa.Float(), nullable=False),
        sa.Column("buying_stage", sa.String(64), nullable=False),
        sa.Column("urgency", sa.String(32), nullable=False),
        sa.Column("budget_probability", sa.String(32), nullable=False),
        sa.Column("decision_window_days", sa.Integer(), nullable=False),
        sa.Column("primary_offer", sa.String(128), nullable=False),
        sa.Column("expected_value", sa.String(64), nullable=False),
        sa.Column("deal_probability", sa.Float(), nullable=False),
        sa.Column("close_probability", sa.Float(), nullable=False),
        sa.Column("sales_health", sa.Float(), nullable=False),
        sa.Column("relationship_health", sa.Float(), nullable=False),
        sa.Column("competition_risk", sa.Float(), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="si-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_sales_intelligence_snapshots_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name=op.f("fk_sales_intelligence_snapshots_opportunity_id_opportunities"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_intelligence_snapshots")),
    )
    op.create_index(
        "ix_si_snapshots_company_created", "sales_intelligence_snapshots", ["company_id", "created_at"]
    )
    op.create_index("ix_si_snapshots_opportunity", "sales_intelligence_snapshots", ["opportunity_id"])
    op.create_index("ix_si_snapshots_intent", "sales_intelligence_snapshots", ["buying_intent_score"])
    op.create_index("ix_si_snapshots_deal", "sales_intelligence_snapshots", ["deal_probability"])

    op.create_table(
        "sales_memory_events",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_key", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("refs", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_sales_memory_events_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_memory_events_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["sales_intelligence_snapshots.id"],
            name=op.f("fk_sales_memory_events_snapshot_id_sales_intelligence_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_memory_events")),
    )
    op.create_index("ix_si_memory_company_occurred", "sales_memory_events", ["company_id", "occurred_at"])
    op.create_index("ix_si_memory_type", "sales_memory_events", ["event_type"])

    op.create_table(
        "sales_reply_intelligence",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reply_ref", sa.String(128), nullable=True),
        sa.Column("classification", sa.String(64), nullable=False),
        sa.Column("best_response", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("reply_text", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_sales_reply_intelligence_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name=op.f("fk_sales_reply_intelligence_opportunity_id_opportunities"),
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["sales_intelligence_snapshots.id"],
            name=op.f("fk_sales_reply_intelligence_snapshot_id_sales_intelligence_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_reply_intelligence")),
    )
    op.create_index("ix_si_reply_company_created", "sales_reply_intelligence", ["company_id", "created_at"])
    op.create_index("ix_si_reply_class", "sales_reply_intelligence", ["classification"])


def downgrade() -> None:
    op.drop_index("ix_si_reply_class", table_name="sales_reply_intelligence")
    op.drop_index("ix_si_reply_company_created", table_name="sales_reply_intelligence")
    op.drop_table("sales_reply_intelligence")
    op.drop_index("ix_si_memory_type", table_name="sales_memory_events")
    op.drop_index("ix_si_memory_company_occurred", table_name="sales_memory_events")
    op.drop_table("sales_memory_events")
    op.drop_index("ix_si_snapshots_deal", table_name="sales_intelligence_snapshots")
    op.drop_index("ix_si_snapshots_intent", table_name="sales_intelligence_snapshots")
    op.drop_index("ix_si_snapshots_opportunity", table_name="sales_intelligence_snapshots")
    op.drop_index("ix_si_snapshots_company_created", table_name="sales_intelligence_snapshots")
    op.drop_table("sales_intelligence_snapshots")
