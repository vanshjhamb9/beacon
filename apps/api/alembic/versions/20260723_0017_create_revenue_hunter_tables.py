"""Create revenue hunter tables.

Revision ID: 20260723_0017
Revises: 20260720_0016
Create Date: 2026-07-23 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0017"
down_revision: str | None = "20260720_0016"
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
        "revenue_hunter_dossiers",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("company_size_band", sa.String(32), nullable=True),
        sa.Column("funding_stage", sa.String(64), nullable=True),
        sa.Column("revenue_band", sa.String(64), nullable=True),
        sa.Column("filter_passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("filter_match", _json(), nullable=False),
        sa.Column("recommended_service", sa.String(128), nullable=False),
        sa.Column("service_confidence", sa.Float(), nullable=False),
        sa.Column("service_matches", _json(), nullable=False),
        sa.Column("pain_points", _json(), nullable=False),
        sa.Column("website_intelligence", _json(), nullable=False),
        sa.Column("why_now", _json(), nullable=False),
        sa.Column("dossier", _json(), nullable=False),
        sa.Column("priority_grade", sa.String(8), nullable=False),
        sa.Column("revenue_score", sa.Float(), nullable=False),
        sa.Column("expected_budget", sa.String(64), nullable=False),
        sa.Column("expected_timeline", sa.String(255), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("proceed_to_campaign", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("work_queue_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("score_breakdown", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("explanations", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_revenue_hunter_dossiers_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            name=op.f("fk_revenue_hunter_dossiers_opportunity_id_opportunities"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_hunter_dossiers")),
    )
    op.create_index("ix_rh_dossiers_grade_score", "revenue_hunter_dossiers", ["priority_grade", "revenue_score"])
    op.create_index("ix_rh_dossiers_company", "revenue_hunter_dossiers", ["company_id"])
    op.create_index(
        "ix_rh_dossiers_campaign", "revenue_hunter_dossiers", ["proceed_to_campaign", "priority_grade"]
    )

    op.create_table(
        "revenue_hunter_work_queue",
        *_base(),
        sa.Column("dossier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("priority_grade", sa.String(8), nullable=False),
        sa.Column("recommended_service", sa.String(128), nullable=False),
        sa.Column("why_today", sa.Text(), nullable=False),
        sa.Column("expected_budget", sa.String(64), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("primary_contact", _json(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("allowed_actions", _json(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("action_log", _json(), nullable=False),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dossier_id"],
            ["revenue_hunter_dossiers.id"],
            name=op.f("fk_revenue_hunter_work_queue_dossier_id_revenue_hunter_dossiers"),
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_revenue_hunter_work_queue_company_id_companies")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_hunter_work_queue")),
    )
    op.create_index("ix_rh_work_queue_status_rank", "revenue_hunter_work_queue", ["status", "rank"])
    op.create_index("ix_rh_work_queue_company", "revenue_hunter_work_queue", ["company_id"])

    op.create_table(
        "revenue_hunter_daily_briefs",
        *_base(),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_pipeline", sa.Float(), nullable=False, server_default="0"),
        sa.Column("meetings_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("campaign_queue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reply_queue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("follow_ups", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hot_opportunities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("top_25", _json(), nullable=False),
        sa.Column("todays_targets", _json(), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_hunter_daily_briefs")),
    )
    op.create_index("ix_rh_daily_briefs_created", "revenue_hunter_daily_briefs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_rh_daily_briefs_created", table_name="revenue_hunter_daily_briefs")
    op.drop_table("revenue_hunter_daily_briefs")
    op.drop_index("ix_rh_work_queue_company", table_name="revenue_hunter_work_queue")
    op.drop_index("ix_rh_work_queue_status_rank", table_name="revenue_hunter_work_queue")
    op.drop_table("revenue_hunter_work_queue")
    op.drop_index("ix_rh_dossiers_campaign", table_name="revenue_hunter_dossiers")
    op.drop_index("ix_rh_dossiers_company", table_name="revenue_hunter_dossiers")
    op.drop_index("ix_rh_dossiers_grade_score", table_name="revenue_hunter_dossiers")
    op.drop_table("revenue_hunter_dossiers")
