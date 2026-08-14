"""add dsip tables

Revision ID: 0080
Revises: 0070
Create Date: 2026-07-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0080"
down_revision = "0070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Source Registry
    op.create_table(
        "dsip_source_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("connector_type", sa.String(100), nullable=False),
        sa.Column("auth_type", sa.String(50), nullable=True),
        sa.Column("auth_config", postgresql.JSONB, nullable=True),
        sa.Column("rate_limit_per_minute", sa.Integer, default=60),
        sa.Column("rate_limit_per_day", sa.Integer, default=10000),
        sa.Column("rate_limit_per_month", sa.Integer, default=300000),
        sa.Column("supported_countries", postgresql.JSONB, nullable=True),
        sa.Column("supported_industries", postgresql.JSONB, nullable=True),
        sa.Column("supported_platforms", postgresql.JSONB, nullable=True),
        sa.Column("supported_languages", postgresql.JSONB, nullable=True),
        sa.Column("average_confidence", sa.Float, default=0.5),
        sa.Column("average_latency_ms", sa.Float, default=0.0),
        sa.Column("cost_per_request", sa.Float, default=0.0),
        sa.Column("monthly_cost_limit", sa.Float, default=0.0),
        sa.Column("current_monthly_cost", sa.Float, default=0.0),
        sa.Column("priority", sa.Integer, default=50),
        sa.Column("freshness_hours", sa.Integer, default=168),
        sa.Column("health_status", sa.String(20), default="unknown"),
        sa.Column("health_score", sa.Float, default=0.0),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_crawl", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer, default=0),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("enabled", sa.Boolean, default=True),
        sa.Column("connector_config", postgresql.JSONB, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Source Reliability
    op.create_table(
        "dsip_source_reliability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("accuracy_score", sa.Float, default=50.0),
        sa.Column("coverage_score", sa.Float, default=50.0),
        sa.Column("freshness_score", sa.Float, default=50.0),
        sa.Column("latency_score", sa.Float, default=50.0),
        sa.Column("reliability_score", sa.Float, default=50.0),
        sa.Column("total_requests", sa.Integer, default=0),
        sa.Column("successful_requests", sa.Integer, default=0),
        sa.Column("failed_requests", sa.Integer, default=0),
        sa.Column("timeout_requests", sa.Integer, default=0),
        sa.Column("total_extracted", sa.Integer, default=0),
        sa.Column("verified_extracted", sa.Integer, default=0),
        sa.Column("conflicted_extracted", sa.Integer, default=0),
        sa.Column("fabricated_detected", sa.Integer, default=0),
        sa.Column("conflict_rate", sa.Float, default=0.0),
        sa.Column("verification_rate", sa.Float, default=0.0),
        sa.Column("fabrication_rate", sa.Float, default=0.0),
        sa.Column("reliability_history", postgresql.JSONB, nullable=True),
        sa.Column("last_calculated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Source Crawl Log
    op.create_table(
        "dsip_source_crawl_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Float, default=0.0),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("companies_found", sa.Integer, default=0),
        sa.Column("companies_accepted", sa.Integer, default=0),
        sa.Column("companies_rejected", sa.Integer, default=0),
        sa.Column("duplicates_found", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("requests_made", sa.Integer, default=0),
        sa.Column("rate_limit_remaining", sa.Integer, default=0),
        sa.Column("cost_incurred", sa.Float, default=0.0),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Discovery Job
    op.create_table(
        "dsip_discovery_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("icp_name", sa.String(255), nullable=True),
        sa.Column("icp_profile", postgresql.JSONB, nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("revenue_min", sa.Float, nullable=True),
        sa.Column("revenue_max", sa.Float, nullable=True),
        sa.Column("company_size_min", sa.Integer, nullable=True),
        sa.Column("company_size_max", sa.Integer, nullable=True),
        sa.Column("technology_filters", postgresql.JSONB, nullable=True),
        sa.Column("pain_filters", postgresql.JSONB, nullable=True),
        sa.Column("intent_filters", postgresql.JSONB, nullable=True),
        sa.Column("negative_icp", postgresql.JSONB, nullable=True),
        sa.Column("sources_selected", postgresql.JSONB, nullable=True),
        sa.Column("sources_used", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("priority", sa.Integer, default=50),
        sa.Column("total_discovered", sa.Integer, default=0),
        sa.Column("total_accepted", sa.Integer, default=0),
        sa.Column("total_rejected", sa.Integer, default=0),
        sa.Column("total_duplicates", sa.Integer, default=0),
        sa.Column("total_queued", sa.Integer, default=0),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Float, default=0.0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Discovered Company
    op.create_table(
        "dsip_discovered_company",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("connector_type", sa.String(100), nullable=False),
        sa.Column("raw_data", postgresql.JSONB, nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("canonical_name", sa.String(255), nullable=True, index=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("primary_domain", sa.String(255), nullable=True, index=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("sub_industry", sa.String(100), nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("business_model", sa.String(50), nullable=True),
        sa.Column("marketplace_presence", sa.Boolean, default=False),
        sa.Column("store_status", sa.String(50), nullable=True),
        sa.Column("store_age_days", sa.Integer, nullable=True),
        sa.Column("estimated_revenue", sa.Float, nullable=True),
        sa.Column("estimated_employees", sa.Integer, nullable=True),
        sa.Column("estimated_traffic", sa.Integer, nullable=True),
        sa.Column("emails", postgresql.JSONB, nullable=True),
        sa.Column("phones", postgresql.JSONB, nullable=True),
        sa.Column("social_profiles", postgresql.JSONB, nullable=True),
        sa.Column("technologies", postgresql.JSONB, nullable=True),
        sa.Column("discovery_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discovery_url", sa.String(1000), nullable=True),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("quality_score", sa.Float, default=0.0),
        sa.Column("quality_grade", sa.String(5), nullable=True),
        sa.Column("quality_issues", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), default="new"),
        sa.Column("rejection_reasons", postgresql.JSONB, nullable=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("duplicate_of", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_canonical", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Canonical Company
    op.create_table(
        "dsip_canonical_company",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("primary_domain", sa.String(255), nullable=False, index=True),
        sa.Column("all_domains", postgresql.JSONB, nullable=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("redirect_chain", postgresql.JSONB, nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("sub_industry", sa.String(100), nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("business_model", sa.String(50), nullable=True),
        sa.Column("marketplace_presence", sa.Boolean, default=False),
        sa.Column("estimated_revenue", sa.Float, nullable=True),
        sa.Column("estimated_employees", sa.Integer, nullable=True),
        sa.Column("estimated_traffic", sa.Integer, nullable=True),
        sa.Column("primary_email", sa.String(255), nullable=True),
        sa.Column("all_emails", postgresql.JSONB, nullable=True),
        sa.Column("primary_phone", sa.String(50), nullable=True),
        sa.Column("all_phones", postgresql.JSONB, nullable=True),
        sa.Column("social_profiles", postgresql.JSONB, nullable=True),
        sa.Column("technologies", postgresql.JSONB, nullable=True),
        sa.Column("tech_stack_confidence", sa.Float, default=0.0),
        sa.Column("decision_makers", postgresql.JSONB, nullable=True),
        sa.Column("discovery_sources", postgresql.JSONB, nullable=True),
        sa.Column("primary_source", sa.String(100), nullable=True),
        sa.Column("first_discovered", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("canonical_confidence", sa.Float, default=0.0),
        sa.Column("identity_confidence", sa.Float, default=0.0),
        sa.Column("data_quality_score", sa.Float, default=0.0),
        sa.Column("discovery_score", sa.Float, default=0.0),
        sa.Column("source_quality", sa.Float, default=0.0),
        sa.Column("evidence_quality", sa.Float, default=0.0),
        sa.Column("website_quality", sa.Float, default=0.0),
        sa.Column("freshness_score", sa.Float, default=0.0),
        sa.Column("activity_score", sa.Float, default=0.0),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("qualified_for_arie", sa.Boolean, default=False),
        sa.Column("arie_classified", sa.String(20), nullable=True),
        sa.Column("merged_from", postgresql.JSONB, nullable=True),
        sa.Column("merge_count", sa.Integer, default=0),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Company Evidence
    op.create_table(
        "dsip_company_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("discovered_company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("field_value", sa.Text, nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("connector_type", sa.String(100), nullable=False),
        sa.Column("evidence_url", sa.String(1000), nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=False),
        sa.Column("extraction_version", sa.String(20), default="1.0"),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verification_method", sa.String(50), nullable=True),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column("first_extracted", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_verified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conflicts_with", postgresql.JSONB, nullable=True),
        sa.Column("is_current", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Freshness Record
    op.create_table(
        "dsip_freshness_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True, unique=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_crawl", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_validated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_name_change", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_tech_change", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact_change", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_traffic_change", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_price_change", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_review_change", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_scheduled_crawl", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawl_frequency_hours", sa.Integer, default=168),
        sa.Column("priority_refresh", sa.Boolean, default=False),
        sa.Column("freshness_score", sa.Float, default=100.0),
        sa.Column("days_since_last_seen", sa.Integer, default=0),
        sa.Column("staleness_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Discovery Queue
    op.create_table(
        "dsip_discovery_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_company_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("discovered_company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("queue_name", sa.String(50), nullable=False, index=True),
        sa.Column("priority", sa.Integer, default=50),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("attempts", sa.Integer, default=0),
        sa.Column("max_attempts", sa.Integer, default=3),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("worker_id", sa.String(100), nullable=True),
        sa.Column("lock_acquired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Discovery Metric
    op.create_table(
        "dsip_discovery_metric",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_name", sa.String(100), nullable=False, index=True),
        sa.Column("metric_type", sa.String(20), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("connector_type", sa.String(100), nullable=True),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Company Merge History
    op.create_table(
        "dsip_company_merge_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("surviving_canonical_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("merged_canonical_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("merge_reason", sa.String(255), nullable=False),
        sa.Column("merge_confidence", sa.Float, nullable=False),
        sa.Column("merge_method", sa.String(50), nullable=False),
        sa.Column("surviving_data_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("merged_data_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("data_conflicts", postgresql.JSONB, nullable=True),
        sa.Column("merged_by", sa.String(100), default="system"),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reversible", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("dsip_company_merge_history")
    op.drop_table("dsip_discovery_metric")
    op.drop_table("dsip_discovery_queue")
    op.drop_table("dsip_freshness_record")
    op.drop_table("dsip_company_evidence")
    op.drop_table("dsip_canonical_company")
    op.drop_table("dsip_discovered_company")
    op.drop_table("dsip_discovery_job")
    op.drop_table("dsip_source_crawl_log")
    op.drop_table("dsip_source_reliability")
    op.drop_table("dsip_source_registry")
