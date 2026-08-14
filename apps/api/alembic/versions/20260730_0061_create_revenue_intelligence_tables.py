"""Create revenue intelligence tables.

Revision ID: 20260730_0061
Revises: 20260730_0060
Create Date: 2026-07-30 02:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0061"
down_revision: str | None = "20260730_0060"
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
        "revenue_intelligence",
        *_base(),
        sa.Column("ecommerce_lead_id", sa.String(64), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False, server_default=""),
        sa.Column("category", sa.String(128), nullable=False, server_default=""),
        sa.Column("country", sa.String(128), nullable=False, server_default="India"),
        sa.Column("pain_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("pain_signals", _json(), nullable=False, server_default="[]"),
        sa.Column("growth_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("growth_signals", _json(), nullable=False, server_default="[]"),
        sa.Column("buying_intent", sa.Float, nullable=False, server_default="0"),
        sa.Column("intent_signals", _json(), nullable=False, server_default="[]"),
        sa.Column("technology_gap", sa.Float, nullable=False, server_default="0"),
        sa.Column("tech_gaps", _json(), nullable=False, server_default="[]"),
        sa.Column("support_gap", sa.Float, nullable=False, server_default="0"),
        sa.Column("support_gaps", _json(), nullable=False, server_default="[]"),
        sa.Column("icp_match", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("icp_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("icp_reasons", _json(), nullable=False, server_default="[]"),
        sa.Column("rejection_reasons", _json(), nullable=False, server_default="[]"),
        sa.Column("revenue_potential", sa.Float, nullable=False, server_default="0"),
        sa.Column("probability_to_buy", sa.Float, nullable=False, server_default="0"),
        sa.Column("probability_reasons", _json(), nullable=False, server_default="[]"),
        sa.Column("why_comai", sa.Text, nullable=False, server_default=""),
        sa.Column("recommended_pitch", sa.Text, nullable=False, server_default=""),
        sa.Column("priority", sa.String(32), nullable=False, server_default="REJECT"),
        sa.Column("traffic_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("review_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("social_growth", sa.Float, nullable=False, server_default="0"),
        sa.Column("whatsapp_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("founder_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("evidence_json", _json(), nullable=False, server_default="[]"),
        sa.Column("product_count", sa.Integer, nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_intelligence")),
    )

    op.create_index("ix_revenue_intelligence_domain", "revenue_intelligence", ["domain"], unique=True)
    op.create_index("ix_revenue_intelligence_priority", "revenue_intelligence", ["priority"])
    op.create_index("ix_revenue_intelligence_probability", "revenue_intelligence", ["probability_to_buy"])
    op.create_index("ix_revenue_intelligence_icp", "revenue_intelligence", ["icp_match"])
    op.create_index("ix_revenue_intelligence_ecommerce_lead", "revenue_intelligence", ["ecommerce_lead_id"])


def downgrade() -> None:
    op.drop_table("revenue_intelligence")
