from uuid import uuid4

from revenue_hunter import RevenueHunterPipeline, RevenueHunterInput, PriorityGrade
from revenue_hunter.dashboard.founder import FounderDashboardBuilder
from revenue_hunter.queue.work_queue import WorkQueueBuilder
from revenue_hunter.models.types import WorkQueueAction


def _hot(**overrides: object) -> RevenueHunterInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Atlas Commerce",
        "industry": "Ecommerce",
        "country": "United States",
        "employee_count": 90,
        "funding_stage": "series_a",
        "funding_days_ago": 14,
        "revenue_band": "SMB",
        "technologies": ["Shopify", "Gorgias", "WhatsApp", "Zendesk"],
        "hiring_roles": ["CX Lead", "Support Agent", "Operations Manager"],
        "hiring_count": 8,
        "pains": ["growing support", "high support cost", "poor conversion", "manual workflows"],
        "signals": ["funding", "hiring", "support growth", "whatsapp"],
        "growth_signals": ["scaling", "repeat orders"],
        "decision_makers": [{"name": "Sam Patel", "role": "COO", "email": "sam@atlas.example", "confidence": 88}],
        "contacts": [{"email": "hello@atlas.example", "type": "email"}],
        "opportunity_score": 88,
        "verification_score": 80,
        "website_metrics": {
            "lcp_ms": 3800,
            "cls": 0.22,
            "seo_score": 42,
            "accessibility_score": 55,
            "has_forms": False,
            "broken_pages": ["/old-promo"],
            "cms": "Shopify",
        },
        "products": ["DTC apparel"],
        "social_profiles": ["linkedin.com/company/atlas"],
    }
    payload.update(overrides)
    return RevenueHunterInput(**payload)  # type: ignore[arg-type]


def test_pipeline_produces_dossier_and_campaign_gate() -> None:
    decision = RevenueHunterPipeline().process(_hot())
    assert decision.filter_match.passed is True
    assert decision.recommended_service
    assert decision.pain_points
    assert decision.website.opportunities
    assert decision.why_now.why_this_company
    assert decision.dossier.proposal_strategy
    assert decision.dossier.meeting_strategy
    assert decision.dossier.case_studies
    assert decision.dossier.decision_makers
    assert decision.evidence_chain
    assert decision.scoring_version == "rh-v1"
    if decision.priority_grade in {PriorityGrade.A_PLUS, PriorityGrade.A}:
        assert decision.proceed_to_campaign is True
        assert decision.work_queue_eligible is True


def test_out_of_market_never_campaigns() -> None:
    decision = RevenueHunterPipeline().process(_hot(country="Brazil", industry="Agriculture", employee_count=5))
    assert decision.filter_match.passed is False
    assert decision.proceed_to_campaign is False
    assert decision.priority_grade in {PriorityGrade.C, PriorityGrade.D, PriorityGrade.B}


def test_work_queue_and_dashboard() -> None:
    d1 = RevenueHunterPipeline().process(_hot())
    d2 = RevenueHunterPipeline().process(_hot(company_name="Beta Soft", industry="SaaS", country="Canada"))
    dossiers = [d1.dossier, d2.dossier]
    queue = WorkQueueBuilder().build(dossiers)
    for item in queue:
        assert item.priority_grade in {PriorityGrade.A_PLUS, PriorityGrade.A}
        assert WorkQueueAction.APPROVE in item.allowed_actions
        updated = WorkQueueBuilder().apply_action(item, WorkQueueAction.APPROVE)
        assert updated.status.value == "approved"
    dashboard = FounderDashboardBuilder().build(dossiers)
    assert dashboard.hot_opportunities >= 0
    assert isinstance(dashboard.expected_revenue, float)
    assert isinstance(dashboard.expected_pipeline, float)
    assert len(dashboard.top_25_companies) <= 25
