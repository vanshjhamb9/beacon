from __future__ import annotations

from revenue_optimization.models.types import ROIPDecision, ROIPInput
from revenue_optimization.pipelines.roip_pipeline import RevenueOptimizationPipeline


class RevenueOptimizationService:
    def __init__(self, pipeline: RevenueOptimizationPipeline | None = None) -> None:
        self.pipeline = pipeline or RevenueOptimizationPipeline()

    def evaluate(self, data: ROIPInput) -> ROIPDecision:
        return self.pipeline.process(data)

    def evaluate_many(self, items: list[ROIPInput]) -> list[ROIPDecision]:
        return [self.evaluate(item) for item in items]

    def search(self, decision: ROIPDecision, *, query: str = "", filters: dict | None = None) -> dict:
        filters = filters or {}
        q = query.strip().lower()
        subjects = [s for s in decision.subjects if not q or q in s.subject.lower()]
        industries = [i for i in decision.industries if not q or q in i.industry.lower()]
        if filters.get("industry"):
            industries = [i for i in industries if i.industry.lower() == str(filters["industry"]).lower()]
        offers = [o for o in decision.offers if not q or q in o.offer.lower()]
        if filters.get("offer"):
            offers = [o for o in offers if o.offer.lower() == str(filters["offer"]).lower()]
        replies = [r for r in decision.replies if not q or q in r.category.value]
        if filters.get("reply_type"):
            replies = [r for r in replies if r.category.value == filters["reply_type"]]
        return {
            "subjects": [s.model_dump(mode="json") for s in subjects],
            "industries": [i.model_dump(mode="json") for i in industries],
            "offers": [o.model_dump(mode="json") for o in offers],
            "replies": [r.model_dump(mode="json") for r in replies],
            "recommendations": [r.model_dump(mode="json") for r in decision.recommendations if not q or q in r.title.lower()],
        }
