from uuid import uuid4

from target_account_engine import TargetAccountPipeline, TargetAccountInput, default_icp_profiles
from target_account_engine.models.types import AccountTier


def _ai_company(**overrides: object) -> TargetAccountInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Northwind Ops",
        "industry": "Software",
        "country": "United States",
        "employee_count": 180,
        "funding_stage": "series_a",
        "funding_amount": 8_000_000,
        "funding_days_ago": 21,
        "technologies": ["HubSpot", "Zendesk", "Salesforce"],
        "hiring_roles": ["Support Engineer", "Operations Analyst", "Customer Success"],
        "hiring_count": 8,
        "pains": ["manual workflows", "repeated manual work", "customer support tools"],
        "goals": ["digital transformation", "automation"],
        "signals": ["funding", "hiring", "ai", "automation", "scaling", "support growth"],
        "business_model": "saas",
        "growth_signals": ["growing fast", "expansion", "scaling"],
        "decision_makers": [{"name": "Alex CTO", "role": "CTO", "confidence": 90}],
        "contacts": [{"email": "alex@northwind.example", "type": "email"}],
        "channels": ["email", "linkedin", "website"],
        "vendors": ["zendesk", "hubspot"],
        "verification_score": 82,
        "opportunity_score": 88,
    }
    payload.update(overrides)
    return TargetAccountInput(**payload)  # type: ignore[arg-type]


def test_default_icps_cover_four_services() -> None:
    keys = {p.key for p in default_icp_profiles()}
    assert keys == {
        "custom_ai_solutions",
        "comai",
        "website_development",
        "mobile_app_development",
    }


def test_pipeline_ranks_ai_icp_as_top_tier() -> None:
    decision = TargetAccountPipeline().process(_ai_company())
    assert decision.matched_icp_key == "custom_ai_solutions"
    assert decision.revenue_opportunity_score >= 70
    assert decision.tier == AccountTier.TOP
    assert decision.proceed_to_copilot is True
    assert decision.why_now
    assert decision.score_breakdown
    assert all(component.explanation for component in decision.score_breakdown)
    assert decision.hunter_triggered is True or decision.revenue_opportunity_score <= 75


def test_comai_ecommerce_match() -> None:
    decision = TargetAccountPipeline().process(
        _ai_company(
            industry="Ecommerce",
            business_model="d2c",
            technologies=["Shopify", "WhatsApp", "Gorgias"],
            pains=["high customer support", "high whatsapp usage", "product catalogue"],
            signals=["support growth", "whatsapp", "repeat orders", "shopify"],
            growth_signals=["growing support team", "repeat orders"],
            hiring_roles=["CX Lead", "Support Agent"],
            employee_count=90,
        )
    )
    assert decision.matched_icp_key == "comai"
    assert decision.service_match == "COMAI"


def test_website_icp_uses_lighthouse() -> None:
    decision = TargetAccountPipeline().process(
        _ai_company(
            industry="Retail",
            technologies=["WordPress"],
            pains=["outdated website", "weak seo", "low conversion"],
            signals=["website redesign", "high traffic", "seo"],
            website_metrics={"lighthouse": 42, "outdated": True, "monthly_visits": 50000},
            hiring_roles=[],
            hiring_count=0,
            funding_days_ago=None,
            funding_amount=None,
        )
    )
    assert decision.matched_icp_key == "website_development"


def test_deterministic_scoring() -> None:
    item = _ai_company()
    pipeline = TargetAccountPipeline()
    a = pipeline.process(item)
    b = pipeline.process(item)
    assert a.revenue_opportunity_score == b.revenue_opportunity_score
    assert a.tier == b.tier
    assert a.why_now == b.why_now
