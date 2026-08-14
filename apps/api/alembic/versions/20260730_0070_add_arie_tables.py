"""add ARIE tables

Revision ID: 0070
Revises: 0069
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0070"
down_revision = "20260730_0062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === ICP Tables ===
    
    op.create_table(
        "arie_icp_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_ai_generated", sa.Boolean, default=False),
        sa.Column("is_template", sa.Boolean, default=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Industry & Vertical
        sa.Column("industries", postgresql.JSON, default=list),
        sa.Column("subcategories", postgresql.JSON, default=list),
        sa.Column("business_models", postgresql.JSON, default=list),
        # Geographic
        sa.Column("countries", postgresql.JSON, default=list),
        sa.Column("states", postgresql.JSON, default=list),
        sa.Column("cities", postgresql.JSON, default=list),
        # Platform & Technology
        sa.Column("platforms", postgresql.JSON, default=list),
        sa.Column("required_technologies", postgresql.JSON, default=list),
        sa.Column("excluded_technologies", postgresql.JSON, default=list),
        sa.Column("preferred_technologies", postgresql.JSON, default=list),
        # Company Size
        sa.Column("min_revenue", sa.Float, nullable=True),
        sa.Column("max_revenue", sa.Float, nullable=True),
        sa.Column("min_employees", sa.Integer, nullable=True),
        sa.Column("max_employees", sa.Integer, nullable=True),
        sa.Column("min_monthly_traffic", sa.Integer, nullable=True),
        sa.Column("max_monthly_traffic", sa.Integer, nullable=True),
        sa.Column("min_monthly_orders", sa.Integer, nullable=True),
        sa.Column("max_monthly_orders", sa.Integer, nullable=True),
        sa.Column("min_avg_order_value", sa.Float, nullable=True),
        sa.Column("max_avg_order_value", sa.Float, nullable=True),
        sa.Column("min_store_age_months", sa.Integer, nullable=True),
        # Growth Signals
        sa.Column("min_growth_rate", sa.Float, nullable=True),
        sa.Column("min_traffic_growth", sa.Float, nullable=True),
        sa.Column("min_review_growth", sa.Float, nullable=True),
        sa.Column("hiring_signals", postgresql.JSON, default=list),
        sa.Column("funding_signals", postgresql.JSON, default=list),
        # Pain Signals
        sa.Column("pain_categories", postgresql.JSON, default=list),
        sa.Column("min_pain_score", sa.Float, nullable=True),
        # Buying Intent
        sa.Column("intent_signals", postgresql.JSON, default=list),
        sa.Column("min_intent_score", sa.Float, nullable=True),
        # Decision Makers
        sa.Column("decision_maker_roles", postgresql.JSON, default=list),
        sa.Column("min_decision_maker_confidence", sa.Float, nullable=True),
        # Scoring Weights
        sa.Column("icp_weight", sa.Float, default=0.15),
        sa.Column("technology_weight", sa.Float, default=0.20),
        sa.Column("growth_weight", sa.Float, default=0.10),
        sa.Column("pain_weight", sa.Float, default=0.15),
        sa.Column("intent_weight", sa.Float, default=0.15),
        sa.Column("revenue_weight", sa.Float, default=0.10),
        sa.Column("decision_maker_weight", sa.Float, default=0.10),
        sa.Column("contact_quality_weight", sa.Float, default=0.05),
        # Negative ICP
        sa.Column("negative_industries", postgresql.JSON, default=list),
        sa.Column("negative_platforms", postgresql.JSON, default=list),
        sa.Column("negative_countries", postgresql.JSON, default=list),
        sa.Column("negative_company_sizes", postgresql.JSON, default=list),
        sa.Column("negative_keywords", postgresql.JSON, default=list),
        # Thresholds
        sa.Column("min_score", sa.Float, default=50.0),
        sa.Column("auto_qualify_score", sa.Float, default=80.0),
        # Settings
        sa.Column("max_results_per_run", sa.Integer, default=100),
        sa.Column("refresh_interval_hours", sa.Integer, default=24),
        sa.Column("enable_auto_discovery", sa.Boolean, default=True),
        # Metadata
        sa.Column("tags", postgresql.JSON, default=list),
        sa.Column("custom_fields", postgresql.JSON, default=dict),
        # Timestamps
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_icp_profiles_owner", "arie_icp_profiles", ["owner_id"])
    op.create_index("arie_icp_profiles_active", "arie_icp_profiles", ["is_active"])
    
    # ICP Profile Versions
    op.create_table(
        "arie_icp_profile_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_icp_profiles.id"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("snapshot", postgresql.JSON, nullable=False),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # ICP Discoveries
    op.create_table(
        "arie_icp_discoveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_icp_profiles.id"), nullable=False),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("total_found", sa.Integer, default=0),
        sa.Column("total_qualified", sa.Integer, default=0),
        sa.Column("total_rejected", sa.Integer, default=0),
        sa.Column("errors", postgresql.JSON, default=list),
        sa.Column("config", postgresql.JSON, default=dict),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_icp_discoveries_profile", "arie_icp_discoveries", ["profile_id"])
    op.create_index("arie_icp_discoveries_status", "arie_icp_discoveries", ["status"])
    
    # ICP Niches
    op.create_table(
        "arie_icp_niches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_icp_niches.id"), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("keywords", postgresql.JSON, default=list),
        sa.Column("platforms", postgresql.JSON, default=list),
        sa.Column("typical_aov", postgresql.JSON, default=dict),
        sa.Column("typical_traffic", postgresql.JSON, default=dict),
        sa.Column("typical_employees", postgresql.JSON, default=dict),
        sa.Column("growth_rate", sa.Float, nullable=True),
        sa.Column("competition_level", sa.String(50), nullable=True),
        sa.Column("comai_fit", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_icp_niches_slug", "arie_icp_niches", ["slug"])
    op.create_index("arie_icp_niches_parent", "arie_icp_niches", ["parent_id"])
    
    # ICP AI Templates
    op.create_table(
        "arie_icp_ai_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("generated_icp", postgresql.JSON, nullable=False),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("use_case", sa.String(255), nullable=True),
        sa.Column("is_public", sa.Boolean, default=False),
        sa.Column("usage_count", sa.Integer, default=0),
        sa.Column("avg_rating", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # === Company DNA Tables ===
    
    op.create_table(
        "arie_company_dna",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("domain", sa.String(255), nullable=False),
        # Business Model
        sa.Column("business_model", sa.String(100), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("subcategory", sa.String(255), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        # Company Size
        sa.Column("revenue_estimate", sa.Float, nullable=True),
        sa.Column("revenue_currency", sa.String(10), default="USD"),
        sa.Column("employee_estimate", sa.Integer, nullable=True),
        sa.Column("monthly_traffic", sa.Integer, nullable=True),
        sa.Column("monthly_orders", sa.Integer, nullable=True),
        sa.Column("avg_order_value", sa.Float, nullable=True),
        sa.Column("store_age_months", sa.Integer, nullable=True),
        # Products & Collections
        sa.Column("product_count", sa.Integer, nullable=True),
        sa.Column("collection_count", sa.Integer, nullable=True),
        sa.Column("price_range", postgresql.JSON, nullable=True),
        sa.Column("top_categories", postgresql.JSON, default=list),
        # Reviews & Reputation
        sa.Column("review_count", sa.Integer, nullable=True),
        sa.Column("review_growth_rate", sa.Float, nullable=True),
        sa.Column("avg_rating", sa.Float, nullable=True),
        # Traffic & Growth
        sa.Column("traffic_trend", sa.String(50), nullable=True),
        sa.Column("traffic_growth_rate", sa.Float, nullable=True),
        sa.Column("traffic_sources", postgresql.JSON, default=dict),
        # Social Media
        sa.Column("social_media", postgresql.JSON, default=dict),
        sa.Column("social_followers", postgresql.JSON, default=dict),
        sa.Column("social_growth_rate", sa.Float, nullable=True),
        # Geographic
        sa.Column("countries", postgresql.JSON, default=list),
        sa.Column("languages", postgresql.JSON, default=list),
        sa.Column("international_presence", sa.Boolean, default=False),
        # Competitors
        sa.Column("competitors", postgresql.JSON, default=list),
        # Technology Stack
        sa.Column("technology_stack", postgresql.JSON, default=dict),
        # Maturity Scores (0-100)
        sa.Column("ai_maturity", sa.Float, default=0.0),
        sa.Column("marketing_maturity", sa.Float, default=0.0),
        sa.Column("support_maturity", sa.Float, default=0.0),
        sa.Column("automation_maturity", sa.Float, default=0.0),
        sa.Column("ecommerce_maturity", sa.Float, default=0.0),
        # Expansion Stage
        sa.Column("expansion_stage", sa.String(50), nullable=True),
        # Risk Assessment
        sa.Column("risk_score", sa.Float, default=0.0),
        sa.Column("risk_factors", postgresql.JSON, default=list),
        # Buying Probability
        sa.Column("buying_probability", sa.Float, default=0.0),
        sa.Column("buying_signals", postgresql.JSON, default=list),
        # ICP Match
        sa.Column("icp_match_score", sa.Float, default=0.0),
        sa.Column("icp_match_details", postgresql.JSON, default=dict),
        # Quality Metrics
        sa.Column("data_completeness", sa.Float, default=0.0),
        sa.Column("data_freshness", sa.DateTime, nullable=True),
        sa.Column("confidence_score", sa.Float, default=0.0),
        # Historical
        sa.Column("first_seen", sa.DateTime, default=sa.func.now()),
        sa.Column("last_enriched", sa.DateTime, nullable=True),
        sa.Column("enrichment_count", sa.Integer, default=0),
        # Timestamps
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_company_dna_domain", "arie_company_dna", ["domain"])
    op.create_index("arie_company_dna_industry", "arie_company_dna", ["industry"])
    op.create_index("arie_company_dna_icp_score", "arie_company_dna", ["icp_match_score"])
    op.create_index("arie_company_dna_buying_prob", "arie_company_dna", ["buying_probability"])
    
    # Company DNA Snapshots
    op.create_table(
        "arie_company_dna_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dna_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_company_dna.id"), nullable=False),
        sa.Column("snapshot", postgresql.JSON, nullable=False),
        sa.Column("changes", postgresql.JSON, default=dict),
        sa.Column("change_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_company_dna_snapshots_dna", "arie_company_dna_snapshots", ["dna_id"])
    
    # Company DNA Change Logs
    op.create_table(
        "arie_company_dna_change_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dna_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_company_dna.id"), nullable=False),
        sa.Column("field", sa.String(255), nullable=False),
        sa.Column("old_value", postgresql.JSON, nullable=True),
        sa.Column("new_value", postgresql.JSON, nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_company_dna_change_logs_dna", "arie_company_dna_change_logs", ["dna_id"])
    
    # Company Signals
    op.create_table(
        "arie_company_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("signal_type", sa.String(100), nullable=False),
        sa.Column("signal_category", sa.String(100), nullable=True),
        sa.Column("signal_value", postgresql.JSON, nullable=False),
        sa.Column("evidence", postgresql.JSON, default=list),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("detected_at", sa.DateTime, default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_company_signals_company", "arie_company_signals", ["company_id"])
    op.create_index("arie_company_signals_domain", "arie_company_signals", ["domain"])
    op.create_index("arie_company_signals_type", "arie_company_signals", ["signal_type"])
    
    # === Revenue Intelligence Tables ===
    
    # Revenue Scores
    op.create_table(
        "arie_revenue_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("icp_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_icp_profiles.id"), nullable=True),
        # 12 Component Scores
        sa.Column("icp_score", sa.Float, default=0.0),
        sa.Column("icp_evidence", postgresql.JSON, default=list),
        sa.Column("icp_confidence", sa.Float, default=0.0),
        sa.Column("technology_fit", sa.Float, default=0.0),
        sa.Column("technology_evidence", postgresql.JSON, default=list),
        sa.Column("technology_confidence", sa.Float, default=0.0),
        sa.Column("growth_score", sa.Float, default=0.0),
        sa.Column("growth_evidence", postgresql.JSON, default=list),
        sa.Column("growth_confidence", sa.Float, default=0.0),
        sa.Column("pain_score", sa.Float, default=0.0),
        sa.Column("pain_evidence", postgresql.JSON, default=list),
        sa.Column("pain_confidence", sa.Float, default=0.0),
        sa.Column("intent_score", sa.Float, default=0.0),
        sa.Column("intent_evidence", postgresql.JSON, default=list),
        sa.Column("intent_confidence", sa.Float, default=0.0),
        sa.Column("revenue_fit", sa.Float, default=0.0),
        sa.Column("revenue_evidence", postgresql.JSON, default=list),
        sa.Column("revenue_confidence", sa.Float, default=0.0),
        sa.Column("decision_maker_score", sa.Float, default=0.0),
        sa.Column("decision_maker_evidence", postgresql.JSON, default=list),
        sa.Column("decision_maker_confidence", sa.Float, default=0.0),
        sa.Column("contact_quality", sa.Float, default=0.0),
        sa.Column("contact_evidence", postgresql.JSON, default=list),
        sa.Column("contact_confidence", sa.Float, default=0.0),
        sa.Column("urgency_score", sa.Float, default=0.0),
        sa.Column("urgency_evidence", postgresql.JSON, default=list),
        sa.Column("urgency_confidence", sa.Float, default=0.0),
        sa.Column("automation_readiness", sa.Float, default=0.0),
        sa.Column("automation_evidence", postgresql.JSON, default=list),
        sa.Column("automation_confidence", sa.Float, default=0.0),
        sa.Column("ai_readiness", sa.Float, default=0.0),
        sa.Column("ai_evidence", postgresql.JSON, default=list),
        sa.Column("ai_confidence", sa.Float, default=0.0),
        sa.Column("support_complexity", sa.Float, default=0.0),
        sa.Column("support_evidence", postgresql.JSON, default=list),
        sa.Column("support_confidence", sa.Float, default=0.0),
        # Composite Scores
        sa.Column("overall_score", sa.Float, default=0.0),
        sa.Column("overall_confidence", sa.Float, default=0.0),
        sa.Column("close_probability", sa.Float, default=0.0),
        sa.Column("expected_arr", sa.Float, default=0.0),
        sa.Column("arr_confidence", sa.Float, default=0.0),
        sa.Column("expected_payback_months", sa.Integer, nullable=True),
        # Classification
        sa.Column("classification", sa.String(50), default="UNSCORED"),
        sa.Column("weights_used", postgresql.JSON, default=dict),
        # Timestamps
        sa.Column("scored_at", sa.DateTime, default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_revenue_scores_company", "arie_revenue_scores", ["company_id"])
    op.create_index("arie_revenue_scores_domain", "arie_revenue_scores", ["domain"])
    op.create_index("arie_revenue_scores_overall", "arie_revenue_scores", ["overall_score"])
    op.create_index("arie_revenue_scores_classification", "arie_revenue_scores", ["classification"])
    
    # Revenue Score Explanations
    op.create_table(
        "arie_revenue_score_explanations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("score_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("arie_revenue_scores.id"), nullable=False),
        sa.Column("component", sa.String(100), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("weighted_score", sa.Float, nullable=False),
        sa.Column("evidence", postgresql.JSON, default=list),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_revenue_score_explanations_score", "arie_revenue_score_explanations", ["score_id"])
    
    # Revenue Score History
    op.create_table(
        "arie_revenue_score_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("classification", sa.String(50), nullable=False),
        sa.Column("component_scores", postgresql.JSON, nullable=False),
        sa.Column("change_delta", sa.Float, nullable=True),
        sa.Column("change_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_revenue_score_history_company", "arie_revenue_score_history", ["company_id"])
    
    # Negative Qualifications
    op.create_table(
        "arie_negative_qualifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("rejection_reason", sa.String(255), nullable=False),
        sa.Column("rejection_category", sa.String(100), nullable=False),
        sa.Column("evidence", postgresql.JSON, default=list),
        sa.Column("confidence", sa.Float, default=1.0),
        sa.Column("is_manual", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_negative_qualifications_domain", "arie_negative_qualifications", ["domain"])
    
    # Sales Copilot Packages
    op.create_table(
        "arie_sales_copilot_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("icp_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("why_this_company", sa.Text, nullable=True),
        sa.Column("why_now", sa.Text, nullable=True),
        sa.Column("pain_summary", postgresql.JSON, default=list),
        sa.Column("technology_summary", postgresql.JSON, default=dict),
        sa.Column("growth_summary", postgresql.JSON, default=dict),
        sa.Column("recommended_pitch", sa.Text, nullable=True),
        sa.Column("roi_estimate", postgresql.JSON, default=dict),
        sa.Column("outreach_strategy", postgresql.JSON, default=dict),
        sa.Column("email_draft", sa.Text, nullable=True),
        sa.Column("whatsapp_message", sa.Text, nullable=True),
        sa.Column("call_script", sa.Text, nullable=True),
        sa.Column("linkedin_message", sa.Text, nullable=True),
        sa.Column("follow_up_plan", postgresql.JSON, default=list),
        sa.Column("competitive_points", postgresql.JSON, default=list),
        sa.Column("confidence_score", sa.Float, default=0.0),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_sales_copilot_packages_company", "arie_sales_copilot_packages", ["company_id"])
    
    # Campaign Results
    op.create_table(
        "arie_campaign_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("emails_sent", sa.Integer, default=0),
        sa.Column("emails_opened", sa.Integer, default=0),
        sa.Column("emails_clicked", sa.Integer, default=0),
        sa.Column("emails_replied", sa.Integer, default=0),
        sa.Column("whatsapp_sent", sa.Integer, default=0),
        sa.Column("whatsapp_replied", sa.Integer, default=0),
        sa.Column("calls_made", sa.Integer, default=0),
        sa.Column("calls_connected", sa.Integer, default=0),
        sa.Column("linkedin_sent", sa.Integer, default=0),
        sa.Column("linkedin_replied", sa.Integer, default=0),
        sa.Column("meetings_booked", sa.Integer, default=0),
        sa.Column("opportunities_created", sa.Integer, default=0),
        sa.Column("deals_won", sa.Integer, default=0),
        sa.Column("deals_lost", sa.Integer, default=0),
        sa.Column("reason_lost", sa.Text, nullable=True),
        sa.Column("time_to_first_reply", sa.Integer, nullable=True),
        sa.Column("time_to_meeting", sa.Integer, nullable=True),
        sa.Column("time_to_close", sa.Integer, nullable=True),
        sa.Column("icp_at_time", postgresql.JSON, nullable=True),
        sa.Column("score_at_time", postgresql.JSON, nullable=True),
        sa.Column("what_worked", sa.Text, nullable=True),
        sa.Column("what_didnt_work", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_campaign_results_campaign", "arie_campaign_results", ["campaign_id"])
    op.create_index("arie_campaign_results_company", "arie_campaign_results", ["company_id"])
    
    # Learning Events
    op.create_table(
        "arie_learning_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning", postgresql.JSON, nullable=False),
        sa.Column("score_impact", postgresql.JSON, nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("is_applied", sa.Boolean, default=False),
        sa.Column("applied_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index("arie_learning_events_type", "arie_learning_events", ["event_type"])
    op.create_index("arie_learning_events_entity", "arie_learning_events", ["entity_type", "entity_id"])
    op.create_index("arie_learning_events_applied", "arie_learning_events", ["is_applied"])


def downgrade() -> None:
    op.drop_table("arie_learning_events")
    op.drop_table("arie_campaign_results")
    op.drop_table("arie_sales_copilot_packages")
    op.drop_table("arie_negative_qualifications")
    op.drop_table("arie_revenue_score_history")
    op.drop_table("arie_revenue_score_explanations")
    op.drop_table("arie_revenue_scores")
    op.drop_table("arie_company_signals")
    op.drop_table("arie_company_dna_change_logs")
    op.drop_table("arie_company_dna_snapshots")
    op.drop_table("arie_company_dna")
    op.drop_table("arie_icp_ai_templates")
    op.drop_table("arie_icp_niches")
    op.drop_table("arie_icp_discoveries")
    op.drop_table("arie_icp_profile_versions")
    op.drop_table("arie_icp_profiles")
