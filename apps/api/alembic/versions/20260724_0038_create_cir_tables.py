"""Create CIR company intelligence tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0038"
down_revision = "20260724_0037"
branch_labels = None
depends_on = None


def _base_cols():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "cir_company_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("erowd_admitted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("founder_queue_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="cir-v1"),
        *_base_cols(),
    )
    op.create_index("ix_cir_company_profiles_company_id", "cir_company_profiles", ["company_id"])
    op.create_index("ix_cir_company_profiles_verdict", "cir_company_profiles", ["verdict"])

    op.create_table(
        "cir_business_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("primary_product", sa.String(512), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base_cols(),
    )
    op.create_index("ix_cir_business_profiles_company_id", "cir_business_profiles", ["company_id"])

    op.create_table(
        "cir_product_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base_cols(),
    )
    op.create_index("ix_cir_product_profiles_company_id", "cir_product_profiles", ["company_id"])

    op.create_table(
        "cir_technology_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("technologies", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base_cols(),
    )
    op.create_index("ix_cir_technology_profiles_company_id", "cir_technology_profiles", ["company_id"])

    op.create_table(
        "cir_buying_signals",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("signals", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base_cols(),
    )
    op.create_index("ix_cir_buying_signals_company_id", "cir_buying_signals", ["company_id"])

    op.create_table(
        "cir_service_matches",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("best_service", sa.String(128), nullable=True),
        sa.Column("matches", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base_cols(),
    )
    op.create_index("ix_cir_service_matches_company_id", "cir_service_matches", ["company_id"])

    op.create_table(
        "cir_revenue_readiness",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("classification", sa.String(64), nullable=False),
        sa.Column("founder_queue_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("breakdown", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="cir-v1"),
        *_base_cols(),
    )
    op.create_index("ix_cir_revenue_readiness_company_id", "cir_revenue_readiness", ["company_id"])
    op.create_index("ix_cir_revenue_readiness_classification", "cir_revenue_readiness", ["classification"])

    op.create_table(
        "cir_opportunity_narratives",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("best_service", sa.String(128), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base_cols(),
    )
    op.create_index("ix_cir_opportunity_narratives_company_id", "cir_opportunity_narratives", ["company_id"])


def downgrade() -> None:
    for table in (
        "cir_opportunity_narratives",
        "cir_revenue_readiness",
        "cir_service_matches",
        "cir_buying_signals",
        "cir_technology_profiles",
        "cir_product_profiles",
        "cir_business_profiles",
        "cir_company_profiles",
    ):
        op.drop_table(table)
