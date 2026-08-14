"""Create identity graph foundation tables (igf-v1)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260724_0040"
down_revision = "20260724_0039"
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
        "igf_resolution_runs",
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("raw_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_events.id"), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_role", sa.String(32), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("admitted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("identity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="igf-v1"),
        *_base(),
    )
    op.create_index("ix_igf_resolution_runs_signal_id", "igf_resolution_runs", ["signal_id"])
    op.create_index("ix_igf_resolution_runs_verdict", "igf_resolution_runs", ["verdict"])
    op.create_index("ix_igf_resolution_runs_domain", "igf_resolution_runs", ["domain"])

    op.create_table(
        "igf_identity_candidates",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("igf_resolution_runs.id"), nullable=True),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("normalized_key", sa.String(255), nullable=False),
        sa.Column("aliases", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("possible_domain", sa.String(255), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_role", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base(),
    )
    op.create_index("ix_igf_identity_candidates_normalized", "igf_identity_candidates", ["normalized_key"])

    op.create_table(
        "igf_identity_evidence",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("igf_resolution_runs.id"), nullable=True),
        sa.Column("canonical_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("field", sa.String(64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("collector", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_base(),
    )
    op.create_index("ix_igf_identity_evidence_field", "igf_identity_evidence", ["field"])
    op.create_index("ix_igf_identity_evidence_canonical", "igf_identity_evidence", ["canonical_id"])

    op.create_table(
        "igf_canonical_companies",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("trade_name", sa.String(255), nullable=False),
        sa.Column("normalized_key", sa.String(255), nullable=False),
        sa.Column("aliases", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("official_domain", sa.String(255), nullable=True),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("linkedin_company_url", sa.String(1024), nullable=True),
        sa.Column("github_organization", sa.String(255), nullable=True),
        sa.Column("crunchbase", sa.String(1024), nullable=True),
        sa.Column("industry", sa.String(128), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("employee_range", sa.String(64), nullable=True),
        sa.Column("founded", sa.String(64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collectors", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("signals", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="igf-v1"),
        *_base(),
    )
    op.create_index("ix_igf_canonical_companies_domain", "igf_canonical_companies", ["official_domain"])
    op.create_index("ix_igf_canonical_companies_status", "igf_canonical_companies", ["status"])
    op.create_index("ix_igf_canonical_companies_normalized", "igf_canonical_companies", ["normalized_key"])
    op.create_index("ix_igf_canonical_companies_company_id", "igf_canonical_companies", ["company_id"])

    op.create_table(
        "igf_funnel_snapshots",
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("signals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("official_websites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_companies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="igf-v1"),
        *_base(),
    )


def downgrade() -> None:
    op.drop_table("igf_funnel_snapshots")
    op.drop_table("igf_canonical_companies")
    op.drop_table("igf_identity_evidence")
    op.drop_table("igf_identity_candidates")
    op.drop_table("igf_resolution_runs")
