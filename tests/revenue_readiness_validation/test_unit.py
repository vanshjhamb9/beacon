"""M1 Revenue Readiness Validation unit tests."""

from __future__ import annotations

from revenue_readiness_validation import SCORING_VERSION
from revenue_readiness_validation.engines.metrics import SuccessMetricsEngine
from revenue_readiness_validation.engines.opportunity import OpportunityExplainabilityEngine
from revenue_readiness_validation.engines.outreach import OutreachInfrastructureEngine


def test_version():
    assert SCORING_VERSION == "m1-v1"


def test_opportunity_hides_unexplained():
    row = OpportunityExplainabilityEngine().audit({"company_name": "X", "opportunity_id": "1"})
    assert row.hide
    assert not row.explainable
    assert "evidence" in row.missing


def test_opportunity_explainable():
    row = OpportunityExplainabilityEngine().audit(
        {
            "opportunity_id": "1",
            "company_id": "c",
            "company_name": "Acme",
            "why_collected": "reddit",
            "why_interesting": "Hiring support automation engineers this quarter",
            "why_now": "urgent hiring",
            "evidence": ["e1"],
            "source": "reddit",
            "collected_at": "2026-07-23",
            "rules_matched": ["hiring"],
        }
    )
    assert row.explainable
    assert not row.hide


def test_success_metrics_targets():
    m = SuccessMetricsEngine().evaluate(
        {
            "collector_uptime": 100,
            "identity_completeness": 96,
            "contact_ready_accounts": 65,
            "sales_ready_accounts": 45,
            "duplicate_rate": 3,
            "fake_companies": 0,
            "missing_source_attribution": 0,
            "founder_queue_with_evidence": 100,
            "unexplained_a_plus": 0,
            "end_to_end_pipeline_success": 96,
        }
    )
    assert all(x.hit for x in m)


def test_success_metrics_miss():
    m = SuccessMetricsEngine().evaluate({"sales_ready_accounts": 10, "duplicate_rate": 20, "fake_companies": 5})
    by = {x.name: x for x in m}
    assert not by["sales_ready_accounts"].hit
    assert not by["duplicate_rate"].hit
    assert not by["fake_companies"].hit


def test_north_star_estimate():
    est = SuccessMetricsEngine().estimated_qualified_per_100(40, 60)
    assert 40 <= est <= 60


def test_outreach_blocks_production():
    r = OutreachInfrastructureEngine().evaluate({"gmail_oauth": False, "email_sandbox": True})
    assert r["production_allowed"] is False
    assert "gmail_oauth" in r["blockers"]


def test_api_import():
    from app.api.routes.revenue_readiness_validation import router

    assert router.prefix == "/revenue-readiness"
