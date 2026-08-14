"""Create account intelligence (AIP) tables.

Revision ID: 20260724_0028
Revises: 20260724_0027
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0028"
down_revision: str | None = "20260724_0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base() -> list:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _json():
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    tables = [
        (
            "aip_account_profiles",
            [
                sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column("company_name", sa.String(255), nullable=False),
                sa.Column("domain", sa.String(255), nullable=True),
                sa.Column("sales_readiness_score", sa.Float(), nullable=False, server_default="0"),
                sa.Column("sales_readiness_category", sa.String(32), nullable=False, server_default="cold"),
                sa.Column("ai_readiness_score", sa.Float(), nullable=False, server_default="0"),
                sa.Column("overall_confidence", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence_chain", _json(), nullable=False),
                sa.Column("scoring_version", sa.String(64), nullable=False, server_default="aip-v1"),
            ],
            [("ix_aip_profiles_company", ["company_id", "created_at"]), ("ix_aip_profiles_name", ["company_name"])],
        ),
        (
            "aip_company_locations",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("label", sa.String(255), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_locations_company", ["company_key", "created_at"])],
        ),
        (
            "aip_company_departments",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("name", sa.String(128), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_departments_company", ["company_key", "created_at"])],
        ),
        (
            "aip_buying_committee",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("full_name", sa.String(255), nullable=False),
                sa.Column("role", sa.String(128), nullable=False),
                sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
                sa.Column("fabricated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_committee_company", ["company_key", "created_at"])],
        ),
        (
            "aip_verified_contacts",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("full_name", sa.String(255), nullable=False),
                sa.Column("business_email", sa.String(255), nullable=True),
                sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
                sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_contacts_company", ["company_key", "created_at"])],
        ),
        (
            "aip_contact_verification",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("field", sa.String(255), nullable=False),
                sa.Column("status", sa.String(64), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_contact_ver_company", ["company_key", "created_at"])],
        ),
        (
            "technology_profiles_aip",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_tech_company", ["company_key", "created_at"])],
        ),
        (
            "website_profiles_v2",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_website_v2_company", ["company_key", "created_at"])],
        ),
        (
            "aip_financial_profiles",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_financial_company", ["company_key", "created_at"])],
        ),
        (
            "aip_business_profiles",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("growth_stage", sa.String(64), nullable=False, server_default="unknown"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_business_company", ["company_key", "created_at"])],
        ),
        (
            "aip_growth_profiles",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_growth_company", ["company_key", "created_at"])],
        ),
        (
            "ai_readiness_reports",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("overall", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_ai_ready_company", ["company_key", "created_at"])],
        ),
        (
            "sales_readiness_reports",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("score", sa.Float(), nullable=False, server_default="0"),
                sa.Column("category", sa.String(32), nullable=False, server_default="cold"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_sales_ready_company", ["company_key", "created_at"])],
        ),
        (
            "aip_relationship_graph_nodes",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("node_id", sa.String(64), nullable=False),
                sa.Column("node_type", sa.String(64), nullable=False),
                sa.Column("label", sa.String(255), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
                sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            ],
            [("ix_aip_rel_nodes_company", ["company_key", "created_at"])],
        ),
        (
            "aip_relationship_graph_edges",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("edge_id", sa.String(64), nullable=False),
                sa.Column("source_id", sa.String(64), nullable=False),
                sa.Column("target_id", sa.String(64), nullable=False),
                sa.Column("relation", sa.String(64), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
                sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            ],
            [("ix_aip_rel_edges_company", ["company_key", "created_at"])],
        ),
        (
            "aip_confidence_reports",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("overall", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_confidence_company", ["company_key", "created_at"])],
        ),
        (
            "aip_verification_history",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("field", sa.String(255), nullable=False),
                sa.Column("status", sa.String(64), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_verhist_company", ["company_key", "created_at"])],
        ),
        (
            "aip_field_sources",
            [
                sa.Column("company_key", sa.String(64), nullable=False),
                sa.Column("field", sa.String(128), nullable=False),
                sa.Column("source", sa.String(128), nullable=False),
                sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_field_sources_company", ["company_key", "created_at"])],
        ),
        (
            "aip_industry_benchmarks",
            [
                sa.Column("industry", sa.String(128), nullable=False),
                sa.Column("payload", _json(), nullable=False),
                sa.Column("evidence", _json(), nullable=False),
            ],
            [("ix_aip_benchmarks_industry", ["industry", "created_at"])],
        ),
    ]

    for name, cols, indexes in tables:
        op.create_table(name, *_base(), *cols, sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{name}")))
        for idx_name, idx_cols in indexes:
            op.create_index(idx_name, name, idx_cols)


def downgrade() -> None:
    for name, idx in [
        ("aip_industry_benchmarks", "ix_aip_benchmarks_industry"),
        ("aip_field_sources", "ix_aip_field_sources_company"),
        ("aip_verification_history", "ix_aip_verhist_company"),
        ("aip_confidence_reports", "ix_aip_confidence_company"),
        ("aip_relationship_graph_edges", "ix_aip_rel_edges_company"),
        ("aip_relationship_graph_nodes", "ix_aip_rel_nodes_company"),
        ("sales_readiness_reports", "ix_aip_sales_ready_company"),
        ("ai_readiness_reports", "ix_aip_ai_ready_company"),
        ("aip_growth_profiles", "ix_aip_growth_company"),
        ("aip_business_profiles", "ix_aip_business_company"),
        ("aip_financial_profiles", "ix_aip_financial_company"),
        ("website_profiles_v2", "ix_aip_website_v2_company"),
        ("technology_profiles_aip", "ix_aip_tech_company"),
        ("aip_contact_verification", "ix_aip_contact_ver_company"),
        ("aip_verified_contacts", "ix_aip_contacts_company"),
        ("aip_buying_committee", "ix_aip_committee_company"),
        ("aip_company_departments", "ix_aip_departments_company"),
        ("aip_company_locations", "ix_aip_locations_company"),
        ("aip_account_profiles", "ix_aip_profiles_company"),
    ]:
        try:
            op.drop_index(idx, table_name=name)
        except Exception:
            pass
        op.drop_table(name)
    op.drop_index("ix_aip_profiles_name", table_name="aip_account_profiles")
