from uuid import uuid4

from revenue_hunter.filters.engine import TargetAccountFilter
from revenue_hunter.filters.taxonomy import (
    COMPANY_SIZE_BANDS,
    FUNDING_STAGES,
    REVENUE_BANDS,
    TARGET_COUNTRIES,
    TARGET_INDUSTRIES,
    default_filter_criteria,
    normalize_country,
    size_band_from_employees,
)
from revenue_hunter.matching.service_match import ServiceMatchEngine
from revenue_hunter.models.types import FilterCriteria, RevenueHunterInput
from revenue_hunter.pain.engine import PainPointEngine
from revenue_hunter.prioritization.engine import PrioritizationEngine
from revenue_hunter.website.intelligence import WebsiteIntelligenceEngine
from revenue_hunter.why_now.engine_v2 import WhyNowEngineV2


def _item(**overrides: object) -> RevenueHunterInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Northwind Ops",
        "industry": "SaaS",
        "country": "USA",
        "employee_count": 120,
        "funding_stage": "Series A",
        "revenue_band": "SMB",
        "funding_days_ago": 21,
        "technologies": ["Zendesk", "HubSpot", "OpenAI"],
        "hiring_roles": ["Support Engineer", "Operations Analyst"],
        "hiring_count": 6,
        "pains": ["manual workflows", "growing support", "no automation"],
        "signals": ["funding", "hiring", "scaling"],
        "decision_makers": [{"name": "Alex", "role": "CTO", "email": "alex@example.com"}],
        "opportunity_score": 82,
        "verification_score": 75,
        "website_metrics": {"lcp_ms": 3200, "cls": 0.18, "seo_score": 48, "has_forms": False},
    }
    payload.update(overrides)
    return RevenueHunterInput(**payload)  # type: ignore[arg-type]


def test_taxonomy_covers_sprint_filters() -> None:
    assert "USA" in TARGET_COUNTRIES
    assert "Saudi Arabia" in TARGET_COUNTRIES
    assert "10-25" in COMPANY_SIZE_BANDS
    assert "500+" in COMPANY_SIZE_BANDS
    assert "SaaS" in TARGET_INDUSTRIES
    assert "Legal" in TARGET_INDUSTRIES
    assert "Bootstrapped" in FUNDING_STAGES
    assert "Public" in FUNDING_STAGES
    assert "Startup" in REVENUE_BANDS
    assert "Enterprise" in REVENUE_BANDS
    assert normalize_country("United States") == "USA"
    assert size_band_from_employees(180) == "100-250"


def test_target_account_filter_pass_and_fail() -> None:
    engine = TargetAccountFilter()
    criteria = default_filter_criteria()
    ok = engine.apply(_item(), criteria)
    assert ok.passed is True
    assert ok.matched_country == "USA"
    bad = engine.apply(_item(country="Brazil", industry="Agriculture"), criteria)
    assert bad.passed is False
    narrow = FilterCriteria(countries=["Canada"], company_sizes=["50-100"], industries=["SaaS"])
    assert engine.apply(_item(country="Canada", employee_count=80), narrow).passed is True


def test_service_match_and_pain_and_website() -> None:
    item = _item()
    services = ServiceMatchEngine().match(item)
    assert services
    assert services[0].confidence >= 35
    assert all(s.evidence for s in services)
    pains = PainPointEngine().analyze(item)
    assert pains
    assert all(p.evidence for p in pains)
    website = WebsiteIntelligenceEngine().analyze(item)
    assert website.opportunities
    assert website.speed_score < 70
    assert "seo" in {o.area for o in website.opportunities} or "speed" in {o.area for o in website.opportunities}


def test_why_now_v2_structured_fields() -> None:
    item = _item()
    filt = TargetAccountFilter().apply(item, default_filter_criteria())
    service = ServiceMatchEngine().match(item)[0]
    pains = PainPointEngine().analyze(item)
    website = WebsiteIntelligenceEngine().analyze(item)
    why = WhyNowEngineV2().generate(item, filter_match=filt, service=service, pains=pains, website=website)
    assert why.why_this_company
    assert why.why_today
    assert why.why_us
    assert why.expected_budget
    assert why.expected_timeline
    assert 5 <= why.probability <= 95
    assert why.evidence_chain


def test_prioritization_campaign_gate() -> None:
    engine = PrioritizationEngine()
    score, breakdown, grade = engine.score(
        filter_passed=True,
        service_confidence=80,
        pain_confidence=70,
        website_opportunity_score=65,
        why_probability=72,
        opportunity_score=80,
        verification_score=75,
        has_decision_maker=True,
    )
    assert breakdown
    assert grade.value in {"A+", "A", "B", "C", "D"}
    if grade.value in {"A+", "A"}:
        assert engine.proceed_to_campaign(grade) is True
    fail_score, _, fail_grade = engine.score(
        filter_passed=False,
        service_confidence=90,
        pain_confidence=90,
        website_opportunity_score=90,
        why_probability=90,
        opportunity_score=90,
        verification_score=90,
        has_decision_maker=True,
    )
    assert fail_score <= 39
    assert engine.proceed_to_campaign(fail_grade) is False
