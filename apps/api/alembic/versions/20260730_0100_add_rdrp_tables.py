"""add rdrp tables

Revision ID: 0100
Revises: 0090
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0100"
down_revision = "0090"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Company Verification
    op.create_table(
        "rdrp_company_verification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("website_alive", sa.Boolean, default=False),
        sa.Column("https_valid", sa.Boolean, default=False),
        sa.Column("homepage_loads", sa.Boolean, default=False),
        sa.Column("about_page_exists", sa.Boolean, default=False),
        sa.Column("contact_page_exists", sa.Boolean, default=False),
        sa.Column("products_exist", sa.Boolean, default=False),
        sa.Column("collection_pages_exist", sa.Boolean, default=False),
        sa.Column("checkout_exists", sa.Boolean, default=False),
        sa.Column("privacy_policy_exists", sa.Boolean, default=False),
        sa.Column("refund_policy_exists", sa.Boolean, default=False),
        sa.Column("terms_exists", sa.Boolean, default=False),
        sa.Column("shipping_policy_exists", sa.Boolean, default=False),
        sa.Column("gst_info_present", sa.Boolean, default=False),
        sa.Column("country_detected", sa.String(100), nullable=True),
        sa.Column("active_ecommerce_store", sa.Boolean, default=False),
        sa.Column("domain_age_days", sa.Integer, nullable=True),
        sa.Column("last_website_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("store_language", sa.String(50), nullable=True),
        sa.Column("store_currency", sa.String(10), nullable=True),
        sa.Column("mobile_responsive", sa.Boolean, default=False),
        sa.Column("verification_score", sa.Float, default=0.0),
        sa.Column("verification_confidence", sa.Float, default=0.0),
        sa.Column("verification_failures", postgresql.JSONB, nullable=True),
        sa.Column("checks_passed", sa.Integer, default=0),
        sa.Column("checks_total", sa.Integer, default=0),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Technology Verification
    op.create_table(
        "rdrp_technology_verification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("technology", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("tech_version", sa.String(50), nullable=True),
        sa.Column("detected", sa.Boolean, default=False),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("evidence_type", sa.String(50), nullable=True),
        sa.Column("evidence_url", sa.String(1000), nullable=True),
        sa.Column("evidence_snapshot", sa.Text, nullable=True),
        sa.Column("script_pattern", sa.String(500), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detection_method", sa.String(50), nullable=True),
        sa.Column("version_detected", sa.Boolean, default=False),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. Company DNA Validation
    op.create_table(
        "rdrp_company_dna_validation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("field_value", sa.Text, nullable=True),
        sa.Column("value_numeric", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_value", sa.Text, nullable=True),
        sa.Column("value_changed", sa.Boolean, default=False),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4. Contact Verification
    op.create_table(
        "rdrp_contact_verification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("contact_type", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("phone_country", sa.String(10), nullable=True),
        sa.Column("phone_type", sa.String(50), nullable=True),
        sa.Column("is_whatsapp", sa.Boolean, default=False),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("evidence_url", sa.String(1000), nullable=True),
        sa.Column("evidence_snapshot", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verification_method", sa.String(50), nullable=True),
        sa.Column("is_disposable", sa.Boolean, default=False),
        sa.Column("is_role_based", sa.Boolean, default=False),
        sa.Column("is_catch_all", sa.Boolean, default=False),
        sa.Column("is_corporate", sa.Boolean, default=False),
        sa.Column("deliverability", sa.String(50), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("reachability_score", sa.Float, default=0.0),
        sa.Column("is_duplicate", sa.Boolean, default=False),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejected", sa.Boolean, default=False),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 5. Evidence
    op.create_table(
        "rdrp_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("field_value", sa.Text, nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("evidence_url", sa.String(1000), nullable=True),
        sa.Column("evidence_snapshot", sa.Text, nullable=True),
        sa.Column("evidence_hash", sa.String(64), nullable=True),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("source_reliability", sa.Float, default=0.5),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 6. Confidence
    op.create_table(
        "rdrp_confidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("confidence_grade", sa.String(5), nullable=True),
        sa.Column("factors", postgresql.JSONB, nullable=True),
        sa.Column("source_count", sa.Integer, default=0),
        sa.Column("source_reliability_avg", sa.Float, default=0.0),
        sa.Column("freshness_score", sa.Float, default=0.0),
        sa.Column("verification_success", sa.Boolean, default=False),
        sa.Column("historical_consistency", sa.Float, default=0.0),
        sa.Column("evidence_quality", sa.Float, default=0.0),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 7. Data Integrity
    op.create_table(
        "rdrp_integrity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("check_type", sa.String(100), nullable=False),
        sa.Column("check_name", sa.String(255), nullable=False),
        sa.Column("passed", sa.Boolean, default=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("affected_fields", postgresql.JSONB, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("auto_fixable", sa.Boolean, default=False),
        sa.Column("auto_fixed", sa.Boolean, default=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 8. Lead Readiness
    op.create_table(
        "rdrp_readiness",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("current_stage", sa.String(50), nullable=False, server_default="DISCOVERED"),
        sa.Column("stage_history", postgresql.JSONB, nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("normalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("company_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tech_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dna_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("icp_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arie_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ricvp_calibrated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sales_ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outreach_ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("block_reason", sa.String(255), nullable=True),
        sa.Column("stages_passed", sa.Integer, default=0),
        sa.Column("stages_total", sa.Integer, default=12),
        sa.Column("readiness_score", sa.Float, default=0.0),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 9. Revenue Reliability Score
    op.create_table(
        "rdrp_reliability_score",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("overall_score", sa.Float, default=0.0),
        sa.Column("overall_grade", sa.String(20), nullable=True),
        sa.Column("company_trust", sa.Float, default=0.0),
        sa.Column("technology_trust", sa.Float, default=0.0),
        sa.Column("contact_trust", sa.Float, default=0.0),
        sa.Column("evidence_trust", sa.Float, default=0.0),
        sa.Column("freshness_score", sa.Float, default=0.0),
        sa.Column("data_completeness", sa.Float, default=0.0),
        sa.Column("verification_success", sa.Float, default=0.0),
        sa.Column("historical_stability", sa.Float, default=0.0),
        sa.Column("confidence_score", sa.Float, default=0.0),
        sa.Column("component_details", postgresql.JSONB, nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB, nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(20), default="v1"),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 10. Verification History
    op.create_table(
        "rdrp_verification_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("verification_type", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("previous_score", sa.Float, nullable=True),
        sa.Column("new_score", sa.Float, nullable=True),
        sa.Column("score_delta", sa.Float, nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("triggered_by", sa.String(50), nullable=True),
        sa.Column("triggered_by_user", sa.String(100), nullable=True),
        sa.Column("record_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("rdrp_verification_history")
    op.drop_table("rdrp_reliability_score")
    op.drop_table("rdrp_readiness")
    op.drop_table("rdrp_integrity")
    op.drop_table("rdrp_confidence")
    op.drop_table("rdrp_evidence")
    op.drop_table("rdrp_contact_verification")
    op.drop_table("rdrp_company_dna_validation")
    op.drop_table("rdrp_technology_verification")
    op.drop_table("rdrp_company_verification")
