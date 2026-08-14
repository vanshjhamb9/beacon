from pathlib import Path

from revenue_optimization import RevenueOptimizationPipeline


def test_regression_compose_only_flags(make_input) -> None:
    d = RevenueOptimizationPipeline().process(make_input(5))
    joined = " ".join(d.evidence_chain)
    assert "compose_only" in joined
    assert "no_gpt" in joined
    assert "never_auto_apply" in joined


def test_regression_append_only_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = (
        root / "apps" / "api" / "alembic" / "versions" / "20260724_0029_create_revenue_optimization_tables.py"
    ).read_text(encoding="utf-8")
    assert "op.drop_table" in migration  # only in downgrade
    assert migration.count("roip_") >= 12
    assert "op.create_table" in migration


def test_regression_worker_tasks_registered() -> None:
    root = Path(__file__).resolve().parents[2]
    celery = (root / "apps" / "worker" / "worker" / "celery_app.py").read_text(encoding="utf-8")
    assert "worker.revenue_optimization_tasks" in celery
    for task in [
        "optimization.collect_metrics",
        "optimization.calculate_scores",
        "optimization.generate_benchmarks",
        "optimization.generate_recommendations",
        "optimization.daily_report",
        "optimization.weekly_report",
    ]:
        assert task in celery


def test_regression_package_modules_exist() -> None:
    root = Path(__file__).resolve().parents[2] / "packages" / "revenue_optimization"
    for part in [
        "email_performance",
        "subject_intelligence",
        "cta_intelligence",
        "followup_intelligence",
        "industry_conversion",
        "founder_performance",
        "offer_intelligence",
        "case_study_intelligence",
        "reply_intelligence",
        "revenue_learning",
        "benchmarks",
        "recommendations",
        "analytics",
        "pipelines",
        "services",
    ]:
        assert (root / part).exists()
