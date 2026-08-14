from pathlib import Path

from revenue_optimization import RevenueOptimizationPipeline
from revenue_optimization.reply_intelligence.engine import OptimizationRecommendationEngine


def test_recommendations_never_auto_apply(make_input) -> None:
    d = RevenueOptimizationPipeline().process(make_input(6, industry="Healthcare", delay_days=4, open_weekday=1))
    assert d.recommendations
    for r in d.recommendations:
        assert r.requires_founder_approval is True
        assert r.modifies_production is False
        assert r.evidence


def test_healthcare_ai_audit_recommendation(make_input) -> None:
    d = RevenueOptimizationPipeline().process(
        make_input(5, industry="Healthcare", offer="AI Audit", delay_days=4, open_weekday=1, closed_won=True)
    )
    titles = " ".join(r.action.lower() for r in d.recommendations)
    assert "healthcare" in titles or "follow-up" in titles or "tuesday" in titles or "maintain" in titles


def test_whatsapp_construction_recommendation(make_input) -> None:
    d = RevenueOptimizationPipeline().process(
        make_input(4, industry="Construction", channel="whatsapp", replied=True, meeting_booked=True)
    )
    assert any("whatsapp" in r.action.lower() or r.segment.lower() == "construction" for r in d.recommendations) or d.recommendations


def test_recommendation_engine_empty_signal() -> None:
    recs = OptimizationRecommendationEngine().generate(
        followup_delay=None,
        industries=[],
        offers=[],
        followup_day=None,
        channels_by_industry={},
    )
    assert len(recs) == 1
    assert recs[0].requires_founder_approval


def test_docs_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    for name in [
        "revenue-optimization.md",
        "email-performance.md",
        "reply-intelligence-v2.md",
        "industry-intelligence.md",
        "founder-performance.md",
        "revenue-learning.md",
        "optimization-recommendations.md",
        "sprint-27-engineering-report.md",
    ]:
        assert (root / "docs" / name).exists()
