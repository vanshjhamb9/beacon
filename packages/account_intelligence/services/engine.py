from __future__ import annotations

from account_intelligence.models.types import AccountIntelligenceDecision, AccountIntelligenceInput
from account_intelligence.pipelines.aip_pipeline import AccountIntelligencePipeline


class AccountIntelligenceService:
    def __init__(self, pipeline: AccountIntelligencePipeline | None = None) -> None:
        self.pipeline = pipeline or AccountIntelligencePipeline()

    def evaluate(self, data: AccountIntelligenceInput) -> AccountIntelligenceDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[AccountIntelligenceInput]) -> list[AccountIntelligenceDecision]:
        return [self.evaluate(item) for item in items]

    def search(
        self,
        decisions: list[AccountIntelligenceDecision],
        *,
        query: str = "",
        filters: dict | None = None,
    ) -> list[AccountIntelligenceDecision]:
        filters = filters or {}
        q = query.strip().lower()
        out: list[AccountIntelligenceDecision] = []
        for d in decisions:
            hay = " ".join(
                [
                    d.company_name,
                    str(d.profile.industry.value or ""),
                    str(d.profile.country.value or ""),
                    " ".join(d.technology.crm + d.technology.ai_stack + d.technology.framework),
                    d.sales_readiness.category.value,
                    " ".join(m.full_name for m in d.buying_committee),
                    " ".join(c.business_email or "" for c in d.verified_contacts),
                    str(d.profile.website.value or ""),
                ]
            ).lower()
            if q and q not in hay:
                continue
            if filters.get("industry") and str(d.profile.industry.value or "").lower() != str(filters["industry"]).lower():
                continue
            if filters.get("country") and str(d.profile.country.value or "").lower() != str(filters["country"]).lower():
                continue
            if filters.get("sales_readiness") and d.sales_readiness.category.value != filters["sales_readiness"]:
                continue
            if filters.get("technology"):
                tech_blob = " ".join(
                    d.technology.frontend + d.technology.backend + d.technology.crm + d.technology.framework
                ).lower()
                if str(filters["technology"]).lower() not in tech_blob:
                    continue
            out.append(d)
        return out
