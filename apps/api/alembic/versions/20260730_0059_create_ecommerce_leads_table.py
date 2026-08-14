"""Create ecommerce leads table.

Revision ID: 20260730_0059
Revises: 20260730_0058
Create Date: 2026-07-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0059"
down_revision: str | None = "20260730_0058"
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
        "ecommerce_leads",
        *_base(),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("industry", sa.String(128), nullable=False, server_default=""),
        sa.Column("category", sa.String(128), nullable=False, server_default=""),
        sa.Column("country", sa.String(128), nullable=False, server_default="India"),
        sa.Column("city", sa.String(128), nullable=False, server_default=""),
        sa.Column("state", sa.String(128), nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("product_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_size", sa.String(64), nullable=False, server_default=""),
        sa.Column("social_links", _json(), nullable=False, server_default="{}"),
        sa.Column("instagram_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("facebook_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("owner_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("founder_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("decision_maker_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("email", sa.String(320), nullable=False, server_default=""),
        sa.Column("phone", sa.String(64), nullable=False, server_default=""),
        sa.Column("contact_source", sa.String(64), nullable=False, server_default=""),
        sa.Column("contact_confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("shopify_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("woocommerce_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("magento_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("chatbot_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("whatsapp_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("crm_detected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("comai_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("lead_priority", sa.String(32), nullable=False, server_default="LOW"),
        sa.Column("sales_reason", sa.Text, nullable=False, server_default=""),
        sa.Column("pain_points", _json(), nullable=False, server_default="[]"),
        sa.Column("source", sa.String(64), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ecommerce_leads")),
    )

    op.create_index("ix_ecommerce_leads_domain", "ecommerce_leads", ["domain"], unique=True)
    op.create_index("ix_ecommerce_leads_country_state", "ecommerce_leads", ["country", "state"])
    op.create_index("ix_ecommerce_leads_platform", "ecommerce_leads", ["platform"])
    op.create_index("ix_ecommerce_leads_score", "ecommerce_leads", ["comai_score"])
    op.create_index("ix_ecommerce_leads_priority", "ecommerce_leads", ["lead_priority"])
    op.create_index("ix_ecommerce_leads_category", "ecommerce_leads", ["category"])


def downgrade() -> None:
    op.drop_table("ecommerce_leads")
