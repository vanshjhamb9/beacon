from revenue_optimization.models.types import ROIPDecision
from revenue_optimization.pipelines.roip_pipeline import RevenueOptimizationPipeline


class AnalyticsFacade:
    """Compose-only analytics summary for dashboards and reports."""

    def summarize(self, decision: ROIPDecision) -> dict:
        return {
            "scoring_version": decision.scoring_version,
            "open_rate": decision.email_metrics.open_rate,
            "reply_rate": decision.email_metrics.reply_rate,
            "revenue": decision.founder.revenue,
            "industries": len(decision.industries),
            "offers": len(decision.offers),
            "recommendations": len(decision.recommendations),
            "benchmarks": len(decision.benchmarks),
            "learning_summary": decision.learning.summary,
            "requires_founder_approval": True,
            "modifies_production": False,
        }


__all__ = ["AnalyticsFacade", "RevenueOptimizationPipeline"]
