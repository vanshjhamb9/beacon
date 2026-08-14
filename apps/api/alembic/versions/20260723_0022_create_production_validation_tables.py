"""Create production validation tables.

Revision ID: 20260723_0022
Revises: 20260723_0021
Create Date: 2026-07-23 21:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0022"
down_revision: str | None = "20260723_0021"
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
        "production_validation_snapshots",
        *_base(),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("overall_status", sa.String(32), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="prrv-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_production_validation_snapshots")),
    )
    op.create_index("ix_prv_snapshots_created", "production_validation_snapshots", ["created_at"])
    op.create_index("ix_prv_snapshots_score", "production_validation_snapshots", ["overall_score"])

    op.create_table(
        "production_alerts",
        *_base(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(128), nullable=False, server_default="founder"),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["production_validation_snapshots.id"],
            name=op.f("fk_production_alerts_snapshot_id_production_validation_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_production_alerts")),
    )
    op.create_index("ix_prv_alerts_severity_created", "production_alerts", ["severity", "created_at"])
    op.create_index("ix_prv_alerts_code", "production_alerts", ["code"])

    op.create_table(
        "lead_readiness_scores",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("outreach_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("checklist", _json(), nullable=False),
        sa.Column("blocking_reasons", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_lead_readiness_scores_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["production_validation_snapshots.id"],
            name=op.f("fk_lead_readiness_scores_snapshot_id_production_validation_snapshots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lead_readiness_scores")),
    )
    op.create_index("ix_prv_lead_company_created", "lead_readiness_scores", ["company_id", "created_at"])
    op.create_index("ix_prv_lead_score", "lead_readiness_scores", ["score"])


def downgrade() -> None:
    op.drop_index("ix_prv_lead_score", table_name="lead_readiness_scores")
    op.drop_index("ix_prv_lead_company_created", table_name="lead_readiness_scores")
    op.drop_table("lead_readiness_scores")
    op.drop_index("ix_prv_alerts_code", table_name="production_alerts")
    op.drop_index("ix_prv_alerts_severity_created", table_name="production_alerts")
    op.drop_table("production_alerts")
    op.drop_index("ix_prv_snapshots_score", table_name="production_validation_snapshots")
    op.drop_index("ix_prv_snapshots_created", table_name="production_validation_snapshots")
    op.drop_table("production_validation_snapshots")
