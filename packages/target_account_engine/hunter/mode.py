from __future__ import annotations

from target_account_engine.models.types import HunterJob, HunterStatus, TargetAccountInput


DEFAULT_HUNTER_TASKS = [
    "enrichment_technology",
    "enrichment_decision_makers",
    "enrichment_funding",
    "enrichment_news",
    "website_audit",
    "enrichment_products",
    "enrichment_customers",
    "enrichment_hiring",
    "enrichment_reviews",
    "enrichment_social_profiles",
]


class HunterMode:
    def __init__(self, *, threshold: float = 75.0) -> None:
        self.threshold = threshold

    def should_trigger(self, revenue_score: float) -> bool:
        return revenue_score > self.threshold

    def plan(self, item: TargetAccountInput, *, revenue_score: float) -> HunterJob | None:
        if not self.should_trigger(revenue_score):
            return None
        tasks = list(DEFAULT_HUNTER_TASKS)
        # Skip tasks already richly present
        if len(item.technologies) >= 5:
            tasks = [t for t in tasks if t != "enrichment_technology"]
        if item.decision_makers:
            tasks = [t for t in tasks if t != "enrichment_decision_makers"]
        if item.funding_stage:
            tasks = [t for t in tasks if t != "enrichment_funding"]
        if item.news:
            tasks = [t for t in tasks if t != "enrichment_news"]
        if item.website_metrics:
            tasks = [t for t in tasks if t != "website_audit"]
        return HunterJob(
            company_id=item.company_id,
            status=HunterStatus.QUEUED,
            tasks=tasks or ["enrichment_refresh"],
        )

    def simulate_run(self, job: HunterJob, item: TargetAccountInput) -> HunterJob:
        """Sandbox/local completion — marks tasks done with evidence snapshots."""
        result = {
            "technologies": list(item.technologies),
            "decision_makers": list(item.decision_makers),
            "funding_stage": item.funding_stage,
            "news": list(item.news),
            "website_metrics": dict(item.website_metrics),
            "products": list(item.products),
            "customers": list(item.customers),
            "hiring_roles": list(item.hiring_roles),
            "reviews": list(item.reviews),
            "social_profiles": list(item.social_profiles),
            "deepened": True,
        }
        return job.model_copy(
            update={
                "status": HunterStatus.COMPLETED,
                "completed_tasks": list(job.tasks),
                "result": result,
            }
        )
