from datetime import UTC, datetime, timedelta
from uuid import uuid4

from outcome_intelligence import OutcomeIntelligencePipeline
from outcome_intelligence.api.contracts import OUTCOME_API_ROUTES
from outcome_intelligence.dashboards.builder import OutcomeDashboardBuilder


def _records() -> list[dict]:
    now = datetime.now(UTC)
    base = {
        "opportunity_id": uuid4(),
        "company_id": uuid4(),
        "opportunity_score": 78.0,
        "recommended_service": "AI Automation",
        "buyer_persona": "CTO",
        "industry": "logistics",
        "collector": "reddit",
        "technology": "Python",
        "decision_maker_role": "CTO",
        "created_at": now - timedelta(days=30),
        "updated_at": now,
    }
    return [
        {**base, "lifecycle_stage": "contacted", "contacted_at": now - timedelta(days=20), "revenue": None},
        {
            **base,
            "lifecycle_stage": "replied",
            "contacted_at": now - timedelta(days=18),
            "replied_at": now - timedelta(days=16),
            "opportunity_score": 70.0,
        },
        {
            **base,
            "lifecycle_stage": "meeting_scheduled",
            "contacted_at": now - timedelta(days=15),
            "replied_at": now - timedelta(days=14),
            "meeting_at": now - timedelta(days=10),
            "opportunity_score": 82.0,
        },
        {
            **base,
            "lifecycle_stage": "proposal_sent",
            "contacted_at": now - timedelta(days=12),
            "proposal_at": now - timedelta(days=5),
            "proposal_value": 25000.0,
            "opportunity_score": 88.0,
        },
        {
            **base,
            "lifecycle_stage": "won",
            "contacted_at": now - timedelta(days=28),
            "close_date": now - timedelta(days=1),
            "revenue": 42000.0,
            "opportunity_score": 91.0,
        },
        {
            **base,
            "lifecycle_stage": "lost",
            "contacted_at": now - timedelta(days=25),
            "close_date": now - timedelta(days=2),
            "revenue": 0.0,
            "opportunity_score": 55.0,
            "collector": "github",
        },
    ]


def test_pipeline_builds_full_dashboard() -> None:
    dashboard = OutcomeIntelligencePipeline().build_dashboard(_records())
    assert dashboard.rates.total_opportunities == 6
    assert dashboard.rates.won_count == 1
    assert dashboard.revenue.total_revenue == 42000.0
    assert dashboard.revenue_by_collector
    assert dashboard.revenue_by_service
    assert dashboard.prediction_accuracy
    assert dashboard.roi["won_deals"] == 1
    assert all(item.requires_approval for item in dashboard.learning_recommendations)


def test_dashboard_builder_surfaces() -> None:
    builder = OutcomeDashboardBuilder()
    records = _records()
    assert builder.sales_funnel(records)
    assert "total_revenue" in builder.revenue_dashboard(records)["revenue"]
    assert isinstance(builder.roi(records)["roi_index"], float)


def test_api_contracts_defined() -> None:
    assert OUTCOME_API_ROUTES["dashboard"].endswith("/outcomes/dashboard")
    assert OUTCOME_API_ROUTES["update"].endswith("/outcomes/update")
    assert "{id}" in OUTCOME_API_ROUTES["company"]
