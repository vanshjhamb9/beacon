"""Create live revenue execution tables.

Revision ID: 20260723_0021
Revises: 20260723_0020
Create Date: 2026-07-23 20:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0021"
down_revision: str | None = "20260723_0020"
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
        "live_revenue_runs",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="lre-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_live_revenue_runs_company_id_companies")),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name=op.f("fk_live_revenue_runs_campaign_id_campaigns")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_live_revenue_runs_opportunity_id_opportunities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_live_revenue_runs")),
    )
    op.create_index("ix_lre_runs_company_created", "live_revenue_runs", ["company_id", "created_at"])
    op.create_index("ix_lre_runs_campaign", "live_revenue_runs", ["campaign_id"])
    op.create_index("ix_lre_runs_stage", "live_revenue_runs", ["stage"])

    op.create_table(
        "live_revenue_lifecycle_events",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_live_revenue_lifecycle_events_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], name=op.f("fk_live_revenue_lifecycle_events_campaign_id_campaigns")
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["live_revenue_runs.id"], name=op.f("fk_live_revenue_lifecycle_events_run_id_live_revenue_runs")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_live_revenue_lifecycle_events")),
    )
    op.create_index(
        "ix_lre_lifecycle_company_occurred", "live_revenue_lifecycle_events", ["company_id", "occurred_at"]
    )
    op.create_index("ix_lre_lifecycle_stage", "live_revenue_lifecycle_events", ["stage"])

    op.create_table(
        "live_revenue_tracking_events",
        *_base(),
        sa.Column("tracking_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_url", sa.Text(), nullable=True),
        sa.Column("provider_response", _json(), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_live_revenue_tracking_events_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], name=op.f("fk_live_revenue_tracking_events_campaign_id_campaigns")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_live_revenue_tracking_events")),
    )
    op.create_index("ix_lre_tracking_id_created", "live_revenue_tracking_events", ["tracking_id", "created_at"])
    op.create_index("ix_lre_tracking_type", "live_revenue_tracking_events", ["event_type"])

    op.create_table(
        "live_revenue_proposal_versions",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("tracking_id", sa.String(64), nullable=False),
        sa.Column("pricing", sa.String(128), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("pdf_base64", sa.Text(), nullable=True),
        sa.Column("opens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_live_revenue_proposal_versions_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], name=op.f("fk_live_revenue_proposal_versions_campaign_id_campaigns")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_live_revenue_proposal_versions")),
    )
    op.create_index("ix_lre_proposal_company_version", "live_revenue_proposal_versions", ["company_id", "version"])
    op.create_index("ix_lre_proposal_tracking", "live_revenue_proposal_versions", ["tracking_id"])


def downgrade() -> None:
    op.drop_index("ix_lre_proposal_tracking", table_name="live_revenue_proposal_versions")
    op.drop_index("ix_lre_proposal_company_version", table_name="live_revenue_proposal_versions")
    op.drop_table("live_revenue_proposal_versions")
    op.drop_index("ix_lre_tracking_type", table_name="live_revenue_tracking_events")
    op.drop_index("ix_lre_tracking_id_created", table_name="live_revenue_tracking_events")
    op.drop_table("live_revenue_tracking_events")
    op.drop_index("ix_lre_lifecycle_stage", table_name="live_revenue_lifecycle_events")
    op.drop_index("ix_lre_lifecycle_company_occurred", table_name="live_revenue_lifecycle_events")
    op.drop_table("live_revenue_lifecycle_events")
    op.drop_index("ix_lre_runs_stage", table_name="live_revenue_runs")
    op.drop_index("ix_lre_runs_campaign", table_name="live_revenue_runs")
    op.drop_index("ix_lre_runs_company_created", table_name="live_revenue_runs")
    op.drop_table("live_revenue_runs")
