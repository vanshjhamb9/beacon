from revenue_optimization import RevenueOptimizationPipeline, RevenueOptimizationService
from revenue_optimization.analytics.engine import AnalyticsFacade
from revenue_optimization.models.types import ROIPInput


def test_analytics_facade(make_input) -> None:
    decision = RevenueOptimizationService().evaluate(make_input(6))
    summary = AnalyticsFacade().summarize(decision)
    assert summary["scoring_version"] == "roip-v1"
    assert summary["requires_founder_approval"] is True
    assert summary["modifies_production"] is False
    assert "open_rate" in summary


def test_analytics_empty() -> None:
    d = RevenueOptimizationPipeline().process(ROIPInput(events=[]))
    summary = AnalyticsFacade().summarize(d)
    assert summary["recommendations"] >= 0
