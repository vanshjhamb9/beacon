"""add ricvp tables

Revision ID: 0090
Revises: 0080
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0090"
down_revision = "0080"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Validation Events
    op.create_table(
        "ricvp_validation_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=True),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("validation_method", sa.String(50), nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False),
        sa.Column("confidence_before", sa.Float, nullable=True),
        sa.Column("confidence_after", sa.Float, nullable=True),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("source_ids", postgresql.JSONB, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Evidence Sources
    op.create_table(
        "ricvp_evidence_source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("field_value", sa.Text, nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("evidence_url", sa.String(1000), nullable=True),
        sa.Column("evidence_snapshot", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verification_method", sa.String(50), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agreeing_sources", sa.Integer, default=1),
        sa.Column("conflicting_sources", sa.Integer, default=0),
        sa.Column("source_reliability", sa.Float, default=0.5),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Field Validation
    op.create_table(
        "ricvp_field_validation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("current_value", sa.Text, nullable=False),
        sa.Column("previous_value", sa.Text, nullable=True),
        sa.Column("validation_status", sa.String(20), default="pending"),
        sa.Column("validation_method", sa.String(50), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("confidence_trend", sa.String(20), nullable=True),
        sa.Column("evidence_count", sa.Integer, default=0),
        sa.Column("agreeing_sources", sa.Integer, default=0),
        sa.Column("conflicting_sources", sa.Integer, default=0),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_verification", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Confidence Scores
    op.create_table(
        "ricvp_confidence_score",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("overall_confidence", sa.Float, default=0.0),
        sa.Column("confidence_grade", sa.String(5), nullable=True),
        sa.Column("discovery_confidence", sa.Float, default=0.0),
        sa.Column("technology_confidence", sa.Float, default=0.0),
        sa.Column("growth_confidence", sa.Float, default=0.0),
        sa.Column("intent_confidence", sa.Float, default=0.0),
        sa.Column("pain_confidence", sa.Float, default=0.0),
        sa.Column("decision_maker_confidence", sa.Float, default=0.0),
        sa.Column("revenue_confidence", sa.Float, default=0.0),
        sa.Column("contact_confidence", sa.Float, default=0.0),
        sa.Column("quality_confidence", sa.Float, default=0.0),
        sa.Column("fields_verified", sa.Integer, default=0),
        sa.Column("fields_total", sa.Integer, default=0),
        sa.Column("evidence_sources", sa.Integer, default=0),
        sa.Column("last_calculated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Calibration History
    op.create_table(
        "ricvp_calibration_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("score_type", sa.String(50), nullable=False),
        sa.Column("raw_score", sa.Float, nullable=False),
        sa.Column("raw_confidence", sa.Float, nullable=False),
        sa.Column("calibration_factor", sa.Float, default=1.0),
        sa.Column("calibration_reason", sa.Text, nullable=True),
        sa.Column("calibrated_score", sa.Float, nullable=False),
        sa.Column("calibrated_confidence", sa.Float, nullable=False),
        sa.Column("predicted_outcome", sa.String(50), nullable=True),
        sa.Column("actual_outcome", sa.String(50), nullable=True),
        sa.Column("prediction_correct", sa.Boolean, nullable=True),
        sa.Column("calibration_model", sa.String(50), default="v1"),
        sa.Column("calibrated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Prediction History
    op.create_table(
        "ricvp_prediction_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("prediction_type", sa.String(50), nullable=False),
        sa.Column("predicted_value", sa.Float, nullable=False),
        sa.Column("predicted_label", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("actual_value", sa.Float, nullable=True),
        sa.Column("actual_label", sa.String(100), nullable=True),
        sa.Column("prediction_error", sa.Float, nullable=True),
        sa.Column("outcome_recorded", sa.Boolean, default=False),
        sa.Column("outcome_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(20), default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Sales Outcomes
    op.create_table(
        "ricvp_sales_outcome",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("previous_stage", sa.String(50), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("lost_reason", sa.String(100), nullable=True),
        sa.Column("competitor_won", sa.String(100), nullable=True),
        sa.Column("deal_value", sa.Float, nullable=True),
        sa.Column("annual_value", sa.Float, nullable=True),
        sa.Column("decision_maker_contacted", sa.String(255), nullable=True),
        sa.Column("contact_method", sa.String(50), nullable=True),
        sa.Column("prediction_at_entry", sa.Float, nullable=True),
        sa.Column("prediction_accuracy", sa.Float, nullable=True),
        sa.Column("engaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_to_close", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Buying Windows
    op.create_table(
        "ricvp_buying_window",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("window_status", sa.String(20), nullable=False),
        sa.Column("window_confidence", sa.Float, default=0.0),
        sa.Column("window_reason", sa.Text, nullable=True),
        sa.Column("hiring_signal", sa.Boolean, default=False),
        sa.Column("funding_signal", sa.Boolean, default=False),
        sa.Column("product_launch_signal", sa.Boolean, default=False),
        sa.Column("tech_migration_signal", sa.Boolean, default=False),
        sa.Column("platform_migration_signal", sa.Boolean, default=False),
        sa.Column("support_growth_signal", sa.Boolean, default=False),
        sa.Column("marketing_expansion_signal", sa.Boolean, default=False),
        sa.Column("holiday_season_signal", sa.Boolean, default=False),
        sa.Column("traffic_growth_signal", sa.Boolean, default=False),
        sa.Column("international_expansion_signal", sa.Boolean, default=False),
        sa.Column("customer_complaints_signal", sa.Boolean, default=False),
        sa.Column("competitor_change_signal", sa.Boolean, default=False),
        sa.Column("ai_adoption_signal", sa.Boolean, default=False),
        sa.Column("website_change_signal", sa.Boolean, default=False),
        sa.Column("pricing_change_signal", sa.Boolean, default=False),
        sa.Column("buying_score", sa.Float, default=0.0),
        sa.Column("urgency_score", sa.Float, default=0.0),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_signal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Competitive Profiles
    op.create_table(
        "ricvp_competitive_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("current_chatbot", sa.String(100), nullable=True),
        sa.Column("current_helpdesk", sa.String(100), nullable=True),
        sa.Column("current_crm", sa.String(100), nullable=True),
        sa.Column("marketing_stack", postgresql.JSONB, nullable=True),
        sa.Column("ai_stack", postgresql.JSONB, nullable=True),
        sa.Column("automation_stack", postgresql.JSONB, nullable=True),
        sa.Column("analytics_stack", postgresql.JSONB, nullable=True),
        sa.Column("payments", postgresql.JSONB, nullable=True),
        sa.Column("shipping", postgresql.JSONB, nullable=True),
        sa.Column("loyalty", postgresql.JSONB, nullable=True),
        sa.Column("subscriptions", postgresql.JSONB, nullable=True),
        sa.Column("technology_gaps", postgresql.JSONB, nullable=True),
        sa.Column("competitive_weaknesses", postgresql.JSONB, nullable=True),
        sa.Column("replacement_opportunities", postgresql.JSONB, nullable=True),
        sa.Column("migration_complexity", sa.String(50), nullable=True),
        sa.Column("switching_cost", sa.String(50), nullable=True),
        sa.Column("competitive_score", sa.Float, default=0.0),
        sa.Column("replacement_probability", sa.Float, default=0.0),
        sa.Column("last_analyzed", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Revenue Estimations
    op.create_table(
        "ricvp_revenue_estimation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("monthly_orders", sa.Integer, nullable=True),
        sa.Column("monthly_visitors", sa.Integer, nullable=True),
        sa.Column("monthly_conversations", sa.Integer, nullable=True),
        sa.Column("support_volume", sa.Integer, nullable=True),
        sa.Column("whatsapp_messages", sa.Integer, nullable=True),
        sa.Column("potential_ai_conversations", sa.Integer, nullable=True),
        sa.Column("expected_arr", sa.Float, default=0.0),
        sa.Column("expansion_revenue", sa.Float, default=0.0),
        sa.Column("upsell_revenue", sa.Float, default=0.0),
        sa.Column("cross_sell_revenue", sa.Float, default=0.0),
        sa.Column("total_opportunity", sa.Float, default=0.0),
        sa.Column("estimated_roi", sa.Float, default=0.0),
        sa.Column("estimated_payback_months", sa.Integer, default=0),
        sa.Column("implementation_complexity", sa.String(50), nullable=True),
        sa.Column("estimation_confidence", sa.Float, default=0.0),
        sa.Column("data_points_used", sa.Integer, default=0),
        sa.Column("estimated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(20), default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Data Drift
    op.create_table(
        "ricvp_data_drift",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("change_type", sa.String(20), nullable=False),
        sa.Column("change_magnitude", sa.Float, default=0.0),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detection_method", sa.String(50), nullable=False),
        sa.Column("impact_score", sa.Float, default=0.0),
        sa.Column("requires_refresh", sa.Boolean, default=False),
        sa.Column("notified", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Field Freshness
    op.create_table(
        "ricvp_field_freshness",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("freshness_score", sa.Float, default=100.0),
        sa.Column("age_hours", sa.Float, default=0.0),
        sa.Column("expected_refresh_hours", sa.Integer, default=168),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_refresh", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("source_reliability", sa.Float, default=0.5),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Score Explanations
    op.create_table(
        "ricvp_score_explanation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("score_type", sa.String(50), nullable=False),
        sa.Column("score_value", sa.Float, nullable=False),
        sa.Column("score_confidence", sa.Float, nullable=False),
        sa.Column("factors", postgresql.JSONB, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("counter_arguments", postgresql.JSONB, nullable=True),
        sa.Column("evidence_count", sa.Integer, default=0),
        sa.Column("evidence_sources", postgresql.JSONB, nullable=True),
        sa.Column("explained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(20), default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ICP Predictions
    op.create_table(
        "ricvp_icp_prediction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("icp_id", sa.String(100), nullable=False),
        sa.Column("predicted_match", sa.Boolean, nullable=False),
        sa.Column("predicted_score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("actual_qualified", sa.Boolean, nullable=True),
        sa.Column("actual_meeting", sa.Boolean, nullable=True),
        sa.Column("actual_deal", sa.Boolean, nullable=True),
        sa.Column("actual_revenue", sa.Float, nullable=True),
        sa.Column("prediction_correct", sa.Boolean, nullable=True),
        sa.Column("calibration_error", sa.Float, nullable=True),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ricvp_icp_prediction")
    op.drop_table("ricvp_score_explanation")
    op.drop_table("ricvp_field_freshness")
    op.drop_table("ricvp_data_drift")
    op.drop_table("ricvp_revenue_estimation")
    op.drop_table("ricvp_competitive_profile")
    op.drop_table("ricvp_buying_window")
    op.drop_table("ricvp_sales_outcome")
    op.drop_table("ricvp_prediction_history")
    op.drop_table("ricvp_calibration_history")
    op.drop_table("ricvp_confidence_score")
    op.drop_table("ricvp_field_validation")
    op.drop_table("ricvp_evidence_source")
    op.drop_table("ricvp_validation_event")
