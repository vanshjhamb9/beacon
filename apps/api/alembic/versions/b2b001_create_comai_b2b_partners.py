"""create comai_b2b_partners table

Revision ID: b2b001
Revises: None
Create Date: 2026-08-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2b001"
down_revision = "07f2c24ee08e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comai_b2b_partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        # Agency basics
        sa.Column("agency_name", sa.String(255), nullable=False),
        sa.Column("agency_url", sa.String(512), server_default=""),
        sa.Column("domain", sa.String(255), server_default=""),
        sa.Column("agency_type", sa.String(64), server_default=""),
        sa.Column("country", sa.String(128), server_default=""),
        sa.Column("city", sa.String(128), server_default=""),

        # Decision maker
        sa.Column("founder_name", sa.String(255), server_default=""),
        sa.Column("founder_role", sa.String(128), server_default=""),
        sa.Column("linkedin_url", sa.String(512), server_default=""),
        sa.Column("identity_confidence", sa.Float, server_default="0"),

        # Services & clients
        sa.Column("services", postgresql.JSONB, server_default="[]"),
        sa.Column("client_count_evidence", sa.Integer, server_default="0"),
        sa.Column("client_examples", postgresql.JSONB, server_default="[]"),
        sa.Column("client_industries", postgresql.JSONB, server_default="[]"),

        # Partner intent
        sa.Column("partner_intent", sa.String(64), server_default="UNKNOWN"),
        sa.Column("partner_intent_evidence", postgresql.JSONB, server_default="[]"),

        # Scoring
        sa.Column("client_access_score", sa.Float, server_default="0"),
        sa.Column("client_access_evidence", postgresql.JSONB, server_default="[]"),
        sa.Column("comai_partner_fit", sa.Float, server_default="0"),
        sa.Column("comai_fit_evidence", postgresql.JSONB, server_default="[]"),

        # Contact
        sa.Column("email", sa.String(320), server_default=""),
        sa.Column("email_status", sa.String(32), server_default="UNKNOWN"),
        sa.Column("email_evidence", postgresql.JSONB, server_default="[]"),
        sa.Column("phone", sa.String(64), server_default=""),
        sa.Column("linkedin_status", sa.String(32), server_default="UNKNOWN"),
        sa.Column("contactability", sa.String(32), server_default="NONE"),
        sa.Column("contactability_evidence", postgresql.JSONB, server_default="[]"),

        # Classification
        sa.Column("partner_tier", sa.String(16), server_default="C"),
        sa.Column("final_verdict", sa.String(32), server_default="NURTURE"),
        sa.Column("rejection_reason", sa.Text, server_default=""),

        # Outreach
        sa.Column("recommended_pitch_angle", sa.Text, server_default=""),
        sa.Column("why_this_agency", sa.Text, server_default=""),
        sa.Column("client_overlap", sa.Text, server_default=""),
        sa.Column("comai_fit_reason", sa.Text, server_default=""),
        sa.Column("partner_opportunity", sa.Text, server_default=""),

        # Safety
        sa.Column("competitor", sa.Boolean, server_default="false"),
        sa.Column("safety_clear", sa.Boolean, server_default="true"),

        # Metadata
        sa.Column("source", sa.String(64), server_default="b2b_partner_extraction"),
        sa.Column("discovery_source", sa.String(64), server_default=""),
        sa.Column("evidence_audit", postgresql.JSONB, server_default="{}"),
    )

    op.create_index("ix_comai_b2b_partners_agency_name", "comai_b2b_partners", ["agency_name"], unique=True)
    op.create_index("ix_comai_b2b_partners_partner_tier", "comai_b2b_partners", ["partner_tier"])
    op.create_index("ix_comai_b2b_partners_client_access_score", "comai_b2b_partners", ["client_access_score"])
    op.create_index("ix_comai_b2b_partners_comai_partner_fit", "comai_b2b_partners", ["comai_partner_fit"])
    op.create_index("ix_comai_b2b_partners_country", "comai_b2b_partners", ["country"])
    op.create_index("ix_comai_b2b_partners_agency_type", "comai_b2b_partners", ["agency_type"])
    op.create_index("ix_comai_b2b_partners_partner_intent", "comai_b2b_partners", ["partner_intent"])
    op.create_index("ix_comai_b2b_partners_final_verdict", "comai_b2b_partners", ["final_verdict"])


def downgrade() -> None:
    op.drop_table("comai_b2b_partners")
