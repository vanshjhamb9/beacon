"""Create revenue data acquisition tables (rdap-v1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0042"
down_revision = "20260724_0041"
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
        "rdap_source_metrics",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("roles", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rdap_source_metrics_connector", "rdap_source_metrics", ["connector"])

    op.create_table(
        "rdap_connector_scores",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("grade", sa.String(32), nullable=False),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("business_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_yield", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rdap_connector_scores_connector", "rdap_connector_scores", ["connector"])

    op.create_table(
        "rdap_company_profiles",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revenue_ready", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("dossier", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rdap-v1"),
        *_base(),
    )
    op.create_index("ix_rdap_company_profiles_company_id", "rdap_company_profiles", ["company_id"])
    op.create_index("ix_rdap_company_profiles_domain", "rdap_company_profiles", ["domain"])

    op.create_table(
        "rdap_contact_recovery",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("email", sa.String(512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("collector", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rdap_contact_recovery_domain", "rdap_contact_recovery", ["domain"])

    op.create_table(
        "rdap_dm_recovery",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_url", sa.String(1024), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rdap_dm_recovery_domain", "rdap_dm_recovery", ["domain"])

    op.create_table(
        "rdap_recovery_queue",
        sa.Column("signal_id", sa.String(128), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )
    op.create_index("ix_rdap_recovery_queue_status", "rdap_recovery_queue", ["status"])

    op.create_table(
        "rdap_revenue_yield",
        sa.Column("connector", sa.String(64), nullable=False),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yield_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_base(),
    )

    op.create_table(
        "rdap_daily_reports",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("business_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decision_makers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_ready", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vansh_ready_answer", sa.String(8), nullable=False, server_default="NO"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="rdap-v1"),
        *_base(),
    )


def downgrade() -> None:
    for t in (
        "rdap_daily_reports",
        "rdap_revenue_yield",
        "rdap_recovery_queue",
        "rdap_dm_recovery",
        "rdap_contact_recovery",
        "rdap_company_profiles",
        "rdap_connector_scores",
        "rdap_source_metrics",
    ):
        op.drop_table(t)
