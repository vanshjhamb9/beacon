"""Create sales intelligence platform tables.

Revision ID: 20260730_0060
Revises: 20260730_0059
Create Date: 2026-07-30 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0060"
down_revision: str | None = "20260730_0059"
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
        "sales_accounts",
        *_base(),
        sa.Column("ecommerce_lead_id", sa.String(64), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False, server_default=""),
        sa.Column("category", sa.String(128), nullable=False, server_default=""),
        sa.Column("country", sa.String(128), nullable=False, server_default="India"),
        sa.Column("city", sa.String(128), nullable=False, server_default=""),
        sa.Column("state", sa.String(128), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="NEEDS_ENRICHMENT"),
        sa.Column("primary_decision_maker", sa.String(255), nullable=False, server_default=""),
        sa.Column("primary_email", sa.String(320), nullable=False, server_default=""),
        sa.Column("primary_phone", sa.String(64), nullable=False, server_default=""),
        sa.Column("primary_linkedin", sa.String(512), nullable=False, server_default=""),
        sa.Column("shopify_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("woocommerce_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("chatbot_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("whatsapp_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("crm_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("pain_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("growth_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("buying_intent", sa.Float, nullable=False, server_default="0"),
        sa.Column("probability_to_buy", sa.Float, nullable=False, server_default="0"),
        sa.Column("revenue_potential", sa.Float, nullable=False, server_default="0"),
        sa.Column("account_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("completeness_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("decision_makers_json", _json(), nullable=False, server_default="[]"),
        sa.Column("contact_channels_json", _json(), nullable=False, server_default="[]"),
        sa.Column("buying_committee_json", _json(), nullable=False, server_default="{}"),
        sa.Column("evidence_json", _json(), nullable=False, server_default="[]"),
        sa.Column("health_json", _json(), nullable=False, server_default="{}"),
        sa.Column("score_json", _json(), nullable=False, server_default="{}"),
        sa.Column("organization_json", _json(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_accounts")),
    )

    op.create_index("ix_sales_accounts_domain", "sales_accounts", ["domain"], unique=True)
    op.create_index("ix_sales_accounts_status", "sales_accounts", ["status"])
    op.create_index("ix_sales_accounts_score", "sales_accounts", ["account_score"])
    op.create_index("ix_sales_accounts_ecommerce_lead", "sales_accounts", ["ecommerce_lead_id"])


def downgrade() -> None:
    op.drop_table("sales_accounts")
