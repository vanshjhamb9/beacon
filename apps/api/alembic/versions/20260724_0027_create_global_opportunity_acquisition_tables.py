"""Create global opportunity acquisition (GOAP) tables.

Revision ID: 20260724_0027
Revises: 20260724_0026
Create Date: 2026-07-24 19:00:00.000000

Note: Spec requested 20260724_0026; that revision is owned by Client Execution (AEP).
GOAP uses 0027 to keep the database append-compatible.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0027"
down_revision: str | None = "20260724_0026"
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
        "source_connectors",
        *_base(),
        sa.Column("connector_id", sa.String(64), nullable=False),
        sa.Column("connector_name", sa.String(128), nullable=False),
        sa.Column("access_mode", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="general"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="goap-v1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_connectors")),
    )
    op.create_index("ix_goap_connectors_connector_id", "source_connectors", ["connector_id"])

    op.create_table(
        "source_runs",
        *_base(),
        sa.Column("connector_id", sa.String(64), nullable=False),
        sa.Column("signals_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("opportunities_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_runs")),
    )
    op.create_index("ix_goap_runs_connector_created", "source_runs", ["connector_id", "created_at"])

    op.create_table(
        "opportunity_graph_nodes",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("node_id", sa.String(64), nullable=False),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_graph_nodes")),
    )
    op.create_index("ix_goap_nodes_company", "opportunity_graph_nodes", ["company_key", "created_at"])

    op.create_table(
        "opportunity_graph_edges",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("edge_id", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_graph_edges")),
    )
    op.create_index("ix_goap_edges_company", "opportunity_graph_edges", ["company_key", "created_at"])

    op.create_table(
        "connector_scores",
        *_base(),
        sa.Column("connector_id", sa.String(64), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("coverage_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("roi_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_connector_scores")),
    )
    op.create_index("ix_goap_scores_connector", "connector_scores", ["connector_id", "created_at"])

    op.create_table(
        "connector_benchmarks",
        *_base(),
        sa.Column("connector_id", sa.String(64), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommendation", sa.String(64), nullable=False, server_default="maintain"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_connector_benchmarks")),
    )
    op.create_index("ix_goap_benchmarks_connector", "connector_benchmarks", ["connector_id", "created_at"])

    op.create_table(
        "website_profiles",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("modernization_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("opportunity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_website_profiles")),
    )
    op.create_index("ix_goap_website_company", "website_profiles", ["company_key", "created_at"])

    op.create_table(
        "technology_profiles",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("technology", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_technology_profiles")),
    )
    op.create_index("ix_goap_tech_company", "technology_profiles", ["company_key", "created_at"])

    op.create_table(
        "funding_events",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("round", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_funding_events")),
    )
    op.create_index("ix_goap_funding_company", "funding_events", ["company_key", "created_at"])

    op.create_table(
        "hiring_events",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("growth", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hiring_events")),
    )
    op.create_index("ix_goap_hiring_company", "hiring_events", ["company_key", "created_at"])

    op.create_table(
        "review_signals",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_signals")),
    )
    op.create_index("ix_goap_reviews_company", "review_signals", ["company_key", "created_at"])

    op.create_table(
        "community_signals",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_signals")),
    )
    op.create_index("ix_goap_community_company", "community_signals", ["company_key", "created_at"])

    op.create_table(
        "procurement_signals",
        *_base(),
        sa.Column("company_key", sa.String(64), nullable=False),
        sa.Column("tender_type", sa.String(64), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_procurement_signals")),
    )
    op.create_index("ix_goap_procurement_company", "procurement_signals", ["company_key", "created_at"])

    op.create_table(
        "source_alerts",
        *_base(),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("connector_id", sa.String(64), nullable=True),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_alerts")),
    )
    op.create_index("ix_goap_alerts_created", "source_alerts", ["created_at"])

    op.create_table(
        "connector_history",
        *_base(),
        sa.Column("connector_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_connector_history")),
    )
    op.create_index("ix_goap_history_connector", "connector_history", ["connector_id", "created_at"])


def downgrade() -> None:
    for table, index in [
        ("connector_history", "ix_goap_history_connector"),
        ("source_alerts", "ix_goap_alerts_created"),
        ("procurement_signals", "ix_goap_procurement_company"),
        ("community_signals", "ix_goap_community_company"),
        ("review_signals", "ix_goap_reviews_company"),
        ("hiring_events", "ix_goap_hiring_company"),
        ("funding_events", "ix_goap_funding_company"),
        ("technology_profiles", "ix_goap_tech_company"),
        ("website_profiles", "ix_goap_website_company"),
        ("connector_benchmarks", "ix_goap_benchmarks_connector"),
        ("connector_scores", "ix_goap_scores_connector"),
        ("opportunity_graph_edges", "ix_goap_edges_company"),
        ("opportunity_graph_nodes", "ix_goap_nodes_company"),
        ("source_runs", "ix_goap_runs_connector_created"),
        ("source_connectors", "ix_goap_connectors_connector_id"),
    ]:
        op.drop_index(index, table_name=table)
        op.drop_table(table)
