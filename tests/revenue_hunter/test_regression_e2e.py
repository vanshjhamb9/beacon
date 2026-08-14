from uuid import uuid4

from revenue_hunter import RevenueHunterPipeline, RevenueHunterInput, BeaconService
from revenue_hunter.filters.taxonomy import TARGET_COUNTRIES, TARGET_INDUSTRIES
from revenue_hunter.models.types import PriorityGrade


def _base(**overrides: object) -> RevenueHunterInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Regression Co",
        "industry": "Technology",
        "country": "UK",
        "employee_count": 200,
        "funding_stage": "Series B",
        "revenue_band": "Mid Market",
        "technologies": ["Salesforce", "OpenAI", "Kubernetes"],
        "pains": ["old technology", "scaling issues", "manual workflows"],
        "signals": ["funding", "hiring", "ai adoption"],
        "hiring_count": 5,
        "hiring_roles": ["Platform Engineer", "ML Engineer"],
        "decision_makers": [{"name": "Jordan", "role": "CTO", "email": "j@ex.com"}],
        "opportunity_score": 78,
        "verification_score": 70,
        "funding_days_ago": 30,
    }
    payload.update(overrides)
    return RevenueHunterInput(**payload)  # type: ignore[arg-type]


def test_deterministic_same_input_same_output() -> None:
    item = _base(company_id=uuid4())
    # freeze company_id
    cid = uuid4()
    a = RevenueHunterPipeline().process(_base(company_id=cid, company_name="Same"))
    b = RevenueHunterPipeline().process(_base(company_id=cid, company_name="Same"))
    assert a.revenue_score == b.revenue_score
    assert a.priority_grade == b.priority_grade
    assert a.recommended_service == b.recommended_service
    assert a.why_now.probability == b.why_now.probability


def test_all_services_reachable() -> None:
    pipeline = RevenueHunterPipeline()
    fixtures = [
        _base(industry="Ecommerce", technologies=["Shopify", "WhatsApp", "Gorgias"], pains=["growing support", "poor conversion"]),
        _base(industry="SaaS", technologies=["OpenAI", "LLM"], pains=["old technology", "no automation"]),
        _base(industry="Marketing", technologies=["WordPress"], pains=["poor website", "poor conversion"]),
        _base(industry="Fintech", technologies=["Flutter", "iOS"], pains=["poor conversion"]),
        _base(industry="Logistics", technologies=["automation", "RPA"], pains=["manual workflows", "no automation"]),
        _base(industry="SaaS", technologies=["multi agent", "agents"], pains=["scaling issues", "no automation"]),
    ]
    services = {pipeline.process(item).recommended_service for item in fixtures}
    assert len(services) >= 3
    assert services & {s.value for s in BeaconService}


def test_only_a_grades_enter_work_queue_path() -> None:
    decision = RevenueHunterPipeline().process(_base())
    if decision.work_queue_eligible:
        assert decision.priority_grade in {PriorityGrade.A_PLUS, PriorityGrade.A}
        assert decision.proceed_to_campaign is True


def test_filter_taxonomy_stable() -> None:
    assert len(TARGET_COUNTRIES) == 9
    assert len(TARGET_INDUSTRIES) == 12
