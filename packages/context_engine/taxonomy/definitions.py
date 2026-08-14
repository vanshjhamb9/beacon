from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaxonomyKind(StrEnum):
    BUSINESS_PAIN = "business_pain"
    TECHNOLOGY = "technology"
    DEPARTMENT = "department"


class TaxonomyTerm(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    kind: TaxonomyKind
    aliases: tuple[str, ...] = ()
    weight: float = Field(default=1.0, ge=0.0, le=2.0)


BUSINESS_PAIN_TERMS: tuple[TaxonomyTerm, ...] = tuple(
    TaxonomyTerm(key=key, label=label, kind=TaxonomyKind.BUSINESS_PAIN, aliases=aliases)
    for key, label, aliases in [
        ("customer_support", "Customer Support", ("support", "help desk", "ticket backlog")),
        ("hiring", "Hiring", ("recruiting", "open roles", "headcount")),
        ("scaling", "Scaling", ("scale", "growth", "capacity")),
        ("operations", "Operations", ("process", "workflow", "ops")),
        ("automation", "Automation", ("automate", "rpa", "workflow automation")),
        ("sales", "Sales", ("pipeline", "revenue", "sales team")),
        ("marketing", "Marketing", ("campaign", "demand gen", "brand")),
        ("finance", "Finance", ("budget", "pricing", "funding")),
        ("logistics", "Logistics", ("shipping", "fulfillment", "warehouse")),
        ("inventory", "Inventory", ("stock", "supply", "sku")),
        ("engineering", "Engineering", ("developer", "platform", "migration")),
        ("security", "Security", ("security", "compliance", "risk")),
        ("compliance", "Compliance", ("regulatory", "audit", "privacy")),
        ("expansion", "Expansion", ("new office", "new market", "international")),
        ("customer_success", "Customer Success", ("retention", "churn", "onboarding")),
    ]
)

TECHNOLOGY_TERMS: tuple[TaxonomyTerm, ...] = tuple(
    TaxonomyTerm(key=key.lower(), label=key, kind=TaxonomyKind.TECHNOLOGY, aliases=aliases)
    for key, aliases in [
        ("Shopify", ("shopify",)),
        ("WooCommerce", ("woocommerce",)),
        ("Magento", ("magento",)),
        ("Salesforce", ("salesforce", "crm")),
        ("HubSpot", ("hubspot",)),
        ("Zendesk", ("zendesk",)),
        ("Freshdesk", ("freshdesk",)),
        ("Intercom", ("intercom",)),
        ("WhatsApp", ("whatsapp",)),
        ("Slack", ("slack",)),
        ("Stripe", ("stripe",)),
        ("Razorpay", ("razorpay",)),
        ("AWS", ("aws", "amazon web services")),
        ("Azure", ("azure",)),
        ("GCP", ("gcp", "google cloud")),
        ("OpenAI", ("openai", "gpt")),
        ("Anthropic", ("anthropic", "claude")),
        ("Gemini", ("gemini",)),
        ("DeepSeek", ("deepseek",)),
        ("Llama", ("llama",)),
    ]
)
