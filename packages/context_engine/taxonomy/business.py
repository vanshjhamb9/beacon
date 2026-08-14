from pydantic import BaseModel, ConfigDict, Field


class ReasoningTaxonomy(BaseModel):
    model_config = ConfigDict(frozen=True)

    pain_by_category: dict[str, str] = Field(
        default_factory=lambda: {
            "customer_support": "customer_support",
            "customer_complaints": "customer_support",
            "hiring": "hiring",
            "funding": "finance",
            "expansion": "expansion",
            "technology_migration": "engineering",
            "ai_adoption": "automation",
            "automation": "automation",
        }
    )
    goal_by_category: dict[str, str] = Field(
        default_factory=lambda: {
            "funding": "deploy_new_capital",
            "expansion": "expand_market_presence",
            "hiring": "increase_operational_capacity",
            "product_launch": "increase_product_adoption",
            "ai_adoption": "improve_intelligence_and_efficiency",
            "automation": "reduce_manual_work",
        }
    )
    trigger_by_category: dict[str, str] = Field(
        default_factory=lambda: {
            "funding": "new_budget_window",
            "customer_complaints": "customer_experience_risk",
            "technology_migration": "platform_change",
            "expansion": "new_market_entry",
            "hiring": "capacity_building",
        }
    )
    impact_by_category: dict[str, str] = Field(
        default_factory=lambda: {
            "expansion": "operational_complexity_increase",
            "hiring": "team_capacity_change",
            "funding": "investment_capacity_increase",
            "product_launch": "go_to_market_motion",
        }
    )
    ai_terms: set[str] = Field(default_factory=lambda: {"openai", "anthropic", "gemini", "deepseek", "llama"})
