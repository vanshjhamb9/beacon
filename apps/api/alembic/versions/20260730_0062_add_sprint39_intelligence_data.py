"""Add Sprint 39 intelligence data to sales_accounts

Revision ID: 20260730_0062
Revises: 20260730_0061
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260730_0062"
down_revision = "20260730_0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sales_accounts",
        sa.Column("technology_profile_json", JSONB, nullable=False, server_default="{}"),
    )
    op.add_column(
        "sales_accounts",
        sa.Column("pain_analysis_json", JSONB, nullable=False, server_default="{}"),
    )
    op.add_column(
        "sales_accounts",
        sa.Column("opportunity_score_json", JSONB, nullable=False, server_default="{}"),
    )
    op.add_column(
        "sales_accounts",
        sa.Column("sales_summary_json", JSONB, nullable=False, server_default="{}"),
    )
    op.add_column(
        "sales_accounts",
        sa.Column("call_preparation_json", JSONB, nullable=False, server_default="{}"),
    )
    op.add_column(
        "sales_accounts",
        sa.Column("website_data_json", JSONB, nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("sales_accounts", "website_data_json")
    op.drop_column("sales_accounts", "call_preparation_json")
    op.drop_column("sales_accounts", "sales_summary_json")
    op.drop_column("sales_accounts", "opportunity_score_json")
    op.drop_column("sales_accounts", "pain_analysis_json")
    op.drop_column("sales_accounts", "technology_profile_json")
