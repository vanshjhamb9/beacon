"""Create account journey / GOI tables.

Revision ID: 20260724_0025
Revises: 20260724_0024
Create Date: 2026-07-24 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0025"
down_revision: str | None = "20260724_0024"
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
        "account_journeys",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("health_category", sa.String(32), nullable=False, server_default="cold"),
        sa.Column("overall_engagement", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="goi-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_account_journeys_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_journeys")),
    )
    op.create_index("ix_goi_journeys_company_created", "account_journeys", ["company_id", "created_at"])
    op.create_index("ix_goi_journeys_stage", "account_journeys", ["stage"])

    op.create_table(
        "engagement_scores",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("open_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("intent_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meeting_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("relationship_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("account_temperature", sa.Float(), nullable=False, server_default="0"),
        sa.Column("overall_engagement", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_engagement_scores_company_id_companies")),
        sa.ForeignKeyConstraint(["journey_id"], ["account_journeys.id"], name=op.f("fk_engagement_scores_journey_id_account_journeys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_engagement_scores")),
    )
    op.create_index("ix_goi_engagement_company_created", "engagement_scores", ["company_id", "created_at"])

    op.create_table(
        "account_health_snapshots",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_account_health_snapshots_company_id_companies")),
        sa.ForeignKeyConstraint(["journey_id"], ["account_journeys.id"], name=op.f("fk_account_health_snapshots_journey_id_account_journeys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_health_snapshots")),
    )
    op.create_index("ix_goi_health_company_created", "account_health_snapshots", ["company_id", "created_at"])

    op.create_table(
        "buying_committees",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("members", _json(), nullable=False),
        sa.Column("missing_roles", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_buying_committees_company_id_companies")),
        sa.ForeignKeyConstraint(["journey_id"], ["account_journeys.id"], name=op.f("fk_buying_committees_journey_id_account_journeys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_buying_committees")),
    )
    op.create_index("ix_goi_committee_company_created", "buying_committees", ["company_id", "created_at"])

    op.create_table(
        "followup_plans",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("next_action", sa.String(128), nullable=False),
        sa.Column("channel", sa.String(64), nullable=False),
        sa.Column("message_type", sa.String(64), nullable=False),
        sa.Column("urgency", sa.String(32), nullable=False, server_default="medium"),
        sa.Column("best_timing_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requires_founder_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_followup_plans_company_id_companies")),
        sa.ForeignKeyConstraint(["journey_id"], ["account_journeys.id"], name=op.f("fk_followup_plans_journey_id_account_journeys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_followup_plans")),
    )
    op.create_index("ix_goi_followup_company_created", "followup_plans", ["company_id", "created_at"])

    op.create_table(
        "reply_classifications",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("classification", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("structured_outcome", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_reply_classifications_company_id_companies")),
        sa.ForeignKeyConstraint(["journey_id"], ["account_journeys.id"], name=op.f("fk_reply_classifications_journey_id_account_journeys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reply_classifications")),
    )
    op.create_index("ix_goi_reply_company_created", "reply_classifications", ["company_id", "created_at"])

    op.create_table(
        "account_timelines",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journey_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_account_timelines_company_id_companies")),
        sa.ForeignKeyConstraint(["journey_id"], ["account_journeys.id"], name=op.f("fk_account_timelines_journey_id_account_journeys")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_account_timelines")),
    )
    op.create_index("ix_goi_timeline_company_occurred", "account_timelines", ["company_id", "occurred_at"])

    op.create_table(
        "campaign_analytics_snapshots",
        *_base(),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="goi-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_analytics_snapshots")),
    )
    op.create_index("ix_goi_analytics_created", "campaign_analytics_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_goi_analytics_created", table_name="campaign_analytics_snapshots")
    op.drop_table("campaign_analytics_snapshots")
    op.drop_index("ix_goi_timeline_company_occurred", table_name="account_timelines")
    op.drop_table("account_timelines")
    op.drop_index("ix_goi_reply_company_created", table_name="reply_classifications")
    op.drop_table("reply_classifications")
    op.drop_index("ix_goi_followup_company_created", table_name="followup_plans")
    op.drop_table("followup_plans")
    op.drop_index("ix_goi_committee_company_created", table_name="buying_committees")
    op.drop_table("buying_committees")
    op.drop_index("ix_goi_health_company_created", table_name="account_health_snapshots")
    op.drop_table("account_health_snapshots")
    op.drop_index("ix_goi_engagement_company_created", table_name="engagement_scores")
    op.drop_table("engagement_scores")
    op.drop_index("ix_goi_journeys_stage", table_name="account_journeys")
    op.drop_index("ix_goi_journeys_company_created", table_name="account_journeys")
    op.drop_table("account_journeys")
