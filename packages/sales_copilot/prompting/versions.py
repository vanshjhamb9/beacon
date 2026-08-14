from __future__ import annotations

from sales_copilot.models.types import LLMProviderName, PromptVersionSpec

PROMPT_V1 = PromptVersionSpec(
    version="sales-copilot-prompt-v1",
    name="Sales Intelligence Package Grounded v1",
    temperature=0.2,
    model_hint="grounded-v1",
    provider_hint=LLMProviderName.GROUNDED,
    system_prompt=(
        "You are Beacon AI Sales Copilot. Generate sales intelligence strictly from verified "
        "Beacon evidence. Never invent company facts, technologies, hiring, revenue, pain points, "
        "or decision makers. If evidence is missing, write exactly: Insufficient verified information. "
        "Every claim must be attributable to provided evidence."
    ),
    user_prompt_template=(
        "Company: {company_name}\n"
        "Recommended service: {recommended_service}\n"
        "Business pain: {business_pain}\n"
        "Evidence:\n{evidence_block}\n"
        "Produce a grounded sales intelligence package and outreach drafts for human review only. "
        "Do not claim any message was sent."
    ),
)

PROMPT_REGISTRY: dict[str, PromptVersionSpec] = {
    PROMPT_V1.version: PROMPT_V1,
}

CURRENT_PROMPT_VERSION = PROMPT_V1.version


def get_prompt_version(version: str | None = None) -> PromptVersionSpec:
    if version and version in PROMPT_REGISTRY:
        return PROMPT_REGISTRY[version]
    return PROMPT_REGISTRY[CURRENT_PROMPT_VERSION]
