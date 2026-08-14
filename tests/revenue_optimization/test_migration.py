from pathlib import Path

from app.models.revenue_optimization import (
    ROIPCTAPerformanceRow,
    ROIPCaseStudyMetricsRow,
    ROIPEmailMetricsRow,
    ROIPFollowupPatternRow,
    ROIPFounderMetricsRow,
    ROIPIndustryMetricsRow,
    ROIPLearningEventRow,
    ROIPOfferMetricsRow,
    ROIPRecommendationRow,
    ROIPReplyAnalysisRow,
    ROIPRevenueBenchmarkRow,
    ROIPSubjectPerformanceRow,
)


def test_roip_tablenames() -> None:
    assert ROIPEmailMetricsRow.__tablename__ == "roip_email_metrics"
    assert ROIPSubjectPerformanceRow.__tablename__ == "roip_subject_performance"
    assert ROIPCTAPerformanceRow.__tablename__ == "roip_cta_performance"
    assert ROIPFollowupPatternRow.__tablename__ == "roip_followup_patterns"
    assert ROIPIndustryMetricsRow.__tablename__ == "roip_industry_metrics"
    assert ROIPFounderMetricsRow.__tablename__ == "roip_founder_metrics"
    assert ROIPOfferMetricsRow.__tablename__ == "roip_offer_metrics"
    assert ROIPCaseStudyMetricsRow.__tablename__ == "roip_case_study_metrics"
    assert ROIPReplyAnalysisRow.__tablename__ == "roip_reply_analysis"
    assert ROIPLearningEventRow.__tablename__ == "roip_learning_events"
    assert ROIPRevenueBenchmarkRow.__tablename__ == "roip_revenue_benchmarks"
    assert ROIPRecommendationRow.__tablename__ == "roip_recommendations"


def test_migration_0029_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260724_0029_create_revenue_optimization_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in [
        "roip_email_metrics",
        "roip_subject_performance",
        "roip_cta_performance",
        "roip_followup_patterns",
        "roip_industry_metrics",
        "roip_founder_metrics",
        "roip_offer_metrics",
        "roip_case_study_metrics",
        "roip_reply_analysis",
        "roip_learning_events",
        "roip_revenue_benchmarks",
        "roip_recommendations",
    ]:
        assert table in text
    assert "20260724_0028" in text
    assert 'revision: str = "20260724_0029"' in text
    assert "requires_founder_approval" in text
    assert "modifies_production" in text


def test_recommendation_defaults() -> None:
    cols = ROIPRecommendationRow.__table__.columns
    assert "requires_founder_approval" in cols
    assert "modifies_production" in cols
