"""Create revenue intelligence tables.

Revision ID: 20260710_0007
Revises: 20260710_0006
Create Date: 2026-07-10 20:05:00.000000
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0007"
down_revision: str | None = "20260710_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column[object]]:
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
        "service_categories",
        sa.Column("category_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_categories")),
    )
    op.create_index("ix_service_categories_key", "service_categories", ["category_key"])

    op.create_table(
        "services",
        sa.Column("service_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_key", sa.String(128), nullable=False),
        sa.Column("base_price", sa.Float(), nullable=False),
        sa.Column("monthly_price", sa.Float(), nullable=False),
        sa.Column("complexity", sa.String(32), nullable=False),
        sa.Column("matching_terms", _json(), nullable=False),
        sa.Column("target_pains", _json(), nullable=False),
        sa.Column("target_industries", _json(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_services")),
    )
    op.create_index("ix_services_key_enabled", "services", ["service_key", "enabled"])

    op.create_table(
        "service_rules",
        sa.Column("service_key", sa.String(128), nullable=False),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("conditions", _json(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_rules")),
    )
    op.create_index("ix_service_rules_service_version", "service_rules", ["service_key", "version"])

    op.create_table(
        "solution_matches",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_service_key", sa.String(128), nullable=False),
        sa.Column("secondary_service_key", sa.String(128), nullable=True),
        sa.Column("cross_sell_service_keys", _json(), nullable=False),
        sa.Column("upsell_service_keys", _json(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_solution_matches_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_solution_matches_opportunity_id_opportunities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solution_matches")),
    )
    op.create_index("ix_solution_matches_company_created", "solution_matches", ["company_id", "created_at"])

    op.create_table(
        "buyer_personas",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_buyer_personas_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_buyer_personas_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_buyer_personas")),
    )
    op.create_index("ix_buyer_personas_company_persona", "buyer_personas", ["company_id", "persona"])

    op.create_table(
        "deal_estimates",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_size", sa.String(64), nullable=False),
        sa.Column("implementation_complexity", sa.String(64), nullable=False),
        sa.Column("estimated_budget_range", sa.String(64), nullable=False),
        sa.Column("priority_level", sa.String(32), nullable=False),
        sa.Column("mrr_potential", sa.Float(), nullable=False),
        sa.Column("one_time_revenue", sa.Float(), nullable=False),
        sa.Column("expansion_potential", sa.Float(), nullable=False),
        sa.Column("renewal_potential", sa.Float(), nullable=False),
        sa.Column("strategic_account_value", sa.Float(), nullable=False),
        sa.Column("revenue_score", sa.Float(), nullable=False),
        sa.Column("urgency", sa.Float(), nullable=False),
        sa.Column("closing_probability", sa.Float(), nullable=False),
        sa.Column("strategic_importance", sa.Float(), nullable=False),
        sa.Column("expected_sales_cycle_days", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_deal_estimates_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_deal_estimates_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_deal_estimates_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deal_estimates")),
    )
    op.create_index("ix_deal_estimates_match_created", "deal_estimates", ["solution_match_id", "created_at"])

    op.create_table(
        "sales_playbooks",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_pain", sa.Text(), nullable=False),
        sa.Column("recommended_service", sa.String(255), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("conversation_angle", sa.Text(), nullable=False),
        sa.Column("decision_maker", sa.String(128), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("risk", sa.Text(), nullable=False),
        sa.Column("playbook", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_sales_playbooks_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_sales_playbooks_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_sales_playbooks_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_playbooks")),
    )
    op.create_index("ix_sales_playbooks_company_created", "sales_playbooks", ["company_id", "created_at"])

    op.create_table(
        "recommendation_history",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_type", sa.String(64), nullable=False),
        sa.Column("recommendation", _json(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_recommendation_history_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recommendation_history")),
    )
    op.create_index(
        "ix_recommendation_history_match_created",
        "recommendation_history",
        ["solution_match_id", "created_at"],
    )

    op.create_table(
        "industry_playbooks",
        sa.Column("industry", sa.String(128), nullable=False),
        sa.Column("service_key", sa.String(128), nullable=False),
        sa.Column("playbook", _json(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_industry_playbooks")),
    )
    op.create_index("ix_industry_playbooks_industry_service", "industry_playbooks", ["industry", "service_key"])

    op.create_table(
        "deal_predictions",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revenue_score", sa.Float(), nullable=False),
        sa.Column("urgency", sa.Float(), nullable=False),
        sa.Column("closing_probability", sa.Float(), nullable=False),
        sa.Column("strategic_importance", sa.Float(), nullable=False),
        sa.Column("customer_lifetime_value", sa.Float(), nullable=False),
        sa.Column("implementation_complexity", sa.Float(), nullable=False),
        sa.Column("priority_level", sa.String(32), nullable=False),
        sa.Column("expected_sales_cycle_days", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_deal_predictions_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["opportunities.id"], name=op.f("fk_deal_predictions_opportunity_id_opportunities")
        ),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_deal_predictions_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deal_predictions")),
    )
    op.create_index("ix_deal_predictions_match_created", "deal_predictions", ["solution_match_id", "created_at"])

    op.create_table(
        "sales_cycles",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expected_days", sa.Integer(), nullable=False),
        sa.Column("stage_plan", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_sales_cycles_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sales_cycles")),
    )
    op.create_index("ix_sales_cycles_match_created", "sales_cycles", ["solution_match_id", "created_at"])

    op.create_table(
        "customer_lifetime_models",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lifetime_value", sa.Float(), nullable=False),
        sa.Column("renewal_probability", sa.Float(), nullable=False),
        sa.Column("expansion_probability", sa.Float(), nullable=False),
        sa.Column("model_details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_customer_lifetime_models_company_id_companies")
        ),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_customer_lifetime_models_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_lifetime_models")),
    )
    op.create_index(
        "ix_customer_lifetime_models_company_created",
        "customer_lifetime_models",
        ["company_id", "created_at"],
    )

    op.create_table(
        "cross_sell_rules",
        sa.Column("service_key", sa.String(128), nullable=False),
        sa.Column("related_service_key", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("conditions", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cross_sell_rules")),
    )
    op.create_index("ix_cross_sell_rules_service", "cross_sell_rules", ["service_key"])

    op.create_table(
        "upsell_rules",
        sa.Column("service_key", sa.String(128), nullable=False),
        sa.Column("upsell_service_key", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("conditions", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_upsell_rules")),
    )
    op.create_index("ix_upsell_rules_service", "upsell_rules", ["service_key"])

    op.create_table(
        "service_feedback",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=False),
        sa.Column("review_outcome", sa.String(64), nullable=False),
        sa.Column("revenue_outcome", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_service_feedback_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_feedback")),
    )
    op.create_index("ix_service_feedback_match_outcome", "service_feedback", ["solution_match_id", "review_outcome"])

    op.create_table(
        "revenue_history",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_revenue_history_company_id_companies")),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_revenue_history_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_history")),
    )
    op.create_index("ix_revenue_history_match_action", "revenue_history", ["solution_match_id", "action"])

    op.create_table(
        "revenue_metrics",
        sa.Column("solution_match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("dimensions", _json(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["solution_match_id"],
            ["solution_matches.id"],
            name=op.f("fk_revenue_metrics_solution_match_id_solution_matches"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_metrics")),
    )
    op.create_index("ix_revenue_metrics_match_name", "revenue_metrics", ["solution_match_id", "metric_name"])

    _seed_services()
    _seed_service_rules()


def _seed_services() -> None:
    services = sa.table(
        "services",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("service_key", sa.String),
        sa.column("name", sa.String),
        sa.column("category_key", sa.String),
        sa.column("base_price", sa.Float),
        sa.column("monthly_price", sa.Float),
        sa.column("complexity", sa.String),
        sa.column("matching_terms", postgresql.JSONB),
        sa.column("target_pains", postgresql.JSONB),
        sa.column("target_industries", postgresql.JSONB),
        sa.column("enabled", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("deleted_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    rows = [
        {
            "service_key": "comai",
            "name": "COMAI",
            "category_key": "ai_platform",
            "base_price": 45000.0,
            "monthly_price": 3500.0,
            "complexity": "high",
            "matching_terms": ["comai", "ai platform", "intelligence platform", "ai product"],
            "target_pains": ["ai", "automation", "operations", "decision_making"],
            "target_industries": ["saas", "software", "fintech", "ecommerce"],
        },
        {
            "service_key": "custom_ai_development",
            "name": "Custom AI Development",
            "category_key": "ai",
            "base_price": 35000.0,
            "monthly_price": 2500.0,
            "complexity": "high",
            "matching_terms": ["custom ai", "machine learning", "llm", "openai", "model", "prediction"],
            "target_pains": ["ai", "automation", "analytics", "decision_making"],
            "target_industries": ["saas", "software", "healthcare", "fintech"],
        },
        {
            "service_key": "ai_automation",
            "name": "AI Automation",
            "category_key": "ai",
            "base_price": 22000.0,
            "monthly_price": 1800.0,
            "complexity": "medium",
            "matching_terms": ["automation", "workflow", "rpa", "process automation", "ai automation"],
            "target_pains": ["automation", "operations", "manual_process", "efficiency"],
            "target_industries": ["saas", "ecommerce", "logistics", "manufacturing"],
        },
        {
            "service_key": "ai_agents",
            "name": "AI Agents",
            "category_key": "ai",
            "base_price": 28000.0,
            "monthly_price": 2200.0,
            "complexity": "high",
            "matching_terms": ["ai agent", "agents", "autonomous", "copilot", "assistant"],
            "target_pains": ["support", "operations", "automation", "productivity"],
            "target_industries": ["saas", "software", "customer_support", "ecommerce"],
        },
        {
            "service_key": "custom_saas",
            "name": "Custom SaaS",
            "category_key": "software",
            "base_price": 40000.0,
            "monthly_price": 3000.0,
            "complexity": "high",
            "matching_terms": ["saas", "platform", "multi-tenant", "subscription product", "web app"],
            "target_pains": ["product", "scaling", "operations", "digital_transformation"],
            "target_industries": ["saas", "software", "b2b"],
        },
        {
            "service_key": "mobile_apps",
            "name": "Mobile Apps",
            "category_key": "software",
            "base_price": 25000.0,
            "monthly_price": 1200.0,
            "complexity": "medium",
            "matching_terms": ["mobile", "ios", "android", "app store", "flutter", "react native"],
            "target_pains": ["mobile", "customer_experience", "engagement", "product"],
            "target_industries": ["ecommerce", "consumer", "fintech", "healthcare"],
        },
        {
            "service_key": "website_development",
            "name": "Website Development",
            "category_key": "web",
            "base_price": 12000.0,
            "monthly_price": 600.0,
            "complexity": "low",
            "matching_terms": ["website", "landing page", "web development", "corporate site"],
            "target_pains": ["marketing", "branding", "lead_generation", "customer_experience"],
            "target_industries": ["services", "ecommerce", "saas", "agency"],
        },
        {
            "service_key": "shopify_development",
            "name": "Shopify Development",
            "category_key": "ecommerce",
            "base_price": 15000.0,
            "monthly_price": 800.0,
            "complexity": "medium",
            "matching_terms": ["shopify", "shopify plus", "storefront", "ecommerce store"],
            "target_pains": ["ecommerce", "checkout", "conversion", "storefront"],
            "target_industries": ["ecommerce", "retail", "dtc"],
        },
        {
            "service_key": "woocommerce_development",
            "name": "WooCommerce Development",
            "category_key": "ecommerce",
            "base_price": 14000.0,
            "monthly_price": 700.0,
            "complexity": "medium",
            "matching_terms": ["woocommerce", "wordpress ecommerce", "wordpress store"],
            "target_pains": ["ecommerce", "checkout", "conversion", "storefront"],
            "target_industries": ["ecommerce", "retail", "dtc"],
        },
        {
            "service_key": "crm_development",
            "name": "CRM Development",
            "category_key": "enterprise",
            "base_price": 30000.0,
            "monthly_price": 2000.0,
            "complexity": "high",
            "matching_terms": ["crm", "salesforce", "hubspot", "pipeline", "customer relationship"],
            "target_pains": ["sales", "pipeline", "customer_management", "retention"],
            "target_industries": ["saas", "b2b", "services", "fintech"],
        },
        {
            "service_key": "erp_development",
            "name": "ERP Development",
            "category_key": "enterprise",
            "base_price": 55000.0,
            "monthly_price": 4000.0,
            "complexity": "high",
            "matching_terms": ["erp", "inventory", "finance system", "operations system", "sap"],
            "target_pains": ["operations", "inventory", "finance", "supply_chain"],
            "target_industries": ["manufacturing", "retail", "logistics", "wholesale"],
        },
        {
            "service_key": "api_integration",
            "name": "API Integration",
            "category_key": "integration",
            "base_price": 18000.0,
            "monthly_price": 900.0,
            "complexity": "medium",
            "matching_terms": ["api", "integration", "webhook", "connector", "middleware"],
            "target_pains": ["integration", "data_silos", "operations", "automation"],
            "target_industries": ["saas", "software", "fintech", "ecommerce"],
        },
        {
            "service_key": "ui_ux",
            "name": "UI/UX",
            "category_key": "design",
            "base_price": 10000.0,
            "monthly_price": 500.0,
            "complexity": "low",
            "matching_terms": ["ui", "ux", "design system", "prototype", "usability", "interface"],
            "target_pains": ["customer_experience", "conversion", "product", "usability"],
            "target_industries": ["saas", "ecommerce", "consumer", "fintech"],
        },
    ]
    op.bulk_insert(
        services,
        [
            {
                "id": uuid4(),
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
                "enabled": True,
                **row,
            }
            for row in rows
        ],
    )


def _seed_service_rules() -> None:
    service_rules = sa.table(
        "service_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("service_key", sa.String),
        sa.column("rule_key", sa.String),
        sa.column("version", sa.Integer),
        sa.column("enabled", sa.Boolean),
        sa.column("priority", sa.Integer),
        sa.column("conditions", postgresql.JSONB),
        sa.column("weight", sa.Float),
        sa.column("explanation", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("deleted_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    rows = [
        {
            "service_key": "custom_ai_development",
            "rule_key": "pain.ai_priority",
            "version": 1,
            "enabled": True,
            "priority": 10,
            "conditions": {"pain_categories": ["ai", "automation", "analytics"]},
            "weight": 1.2,
            "explanation": "Boost Custom AI when AI or automation pains are present.",
        },
        {
            "service_key": "ai_automation",
            "rule_key": "pain.operations_automation",
            "version": 1,
            "enabled": True,
            "priority": 20,
            "conditions": {"pain_categories": ["automation", "operations", "manual_process"]},
            "weight": 1.15,
            "explanation": "Boost AI Automation for operations and workflow pains.",
        },
        {
            "service_key": "shopify_development",
            "rule_key": "industry.ecommerce_shopify",
            "version": 1,
            "enabled": True,
            "priority": 30,
            "conditions": {"industries": ["ecommerce", "retail", "dtc"], "terms": ["shopify"]},
            "weight": 1.25,
            "explanation": "Boost Shopify Development for ecommerce stack signals.",
        },
        {
            "service_key": "crm_development",
            "rule_key": "pain.sales_pipeline",
            "version": 1,
            "enabled": True,
            "priority": 40,
            "conditions": {"pain_categories": ["sales", "pipeline", "retention"]},
            "weight": 1.2,
            "explanation": "Boost CRM Development when sales pipeline pain is evident.",
        },
        {
            "service_key": "api_integration",
            "rule_key": "pain.integration",
            "version": 1,
            "enabled": True,
            "priority": 50,
            "conditions": {"pain_categories": ["integration", "data_silos", "automation"]},
            "weight": 1.1,
            "explanation": "Boost API Integration when systems fragmentation is present.",
        },
    ]
    op.bulk_insert(
        service_rules,
        [
            {
                "id": uuid4(),
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
                **row,
            }
            for row in rows
        ],
    )


def downgrade() -> None:
    for table in [
        "revenue_metrics",
        "revenue_history",
        "service_feedback",
        "upsell_rules",
        "cross_sell_rules",
        "customer_lifetime_models",
        "sales_cycles",
        "deal_predictions",
        "industry_playbooks",
        "recommendation_history",
        "sales_playbooks",
        "deal_estimates",
        "buyer_personas",
        "solution_matches",
        "service_rules",
        "services",
        "service_categories",
    ]:
        op.drop_table(table)
