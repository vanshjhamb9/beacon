"""Create Revenue Readiness Perfection tables (rrp-v1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0044"
down_revision = "20260724_0043"
branch_labels = None
depends_on = None


def _base():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "rrp_company_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revenue_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sales_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trust", sa.Float(), nullable=False, server_default="0"),
        sa.Column("blockers", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("opportunity", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("decision_maker", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("contacts", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rrp-v1"),
        *_base(),
    )
    op.create_index("ix_rrp_company_profiles_company_id", "rrp_company_profiles", ["company_id"])

    op.create_table(
        "rrp_founder_reviews",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )

    op.create_table(
        "rrp_daily_reports",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vansh_ready_answer", sa.String(8), nullable=False, server_default="NO"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rrp-v1"),
        *_base(),
    )


def downgrade() -> None:
    op.drop_table("rrp_daily_reports")
    op.drop_table("rrp_founder_reviews")
    op.drop_table("rrp_company_profiles")
