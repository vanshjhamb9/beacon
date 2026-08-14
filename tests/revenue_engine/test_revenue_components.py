from revenue_engine.buyer_personas.engine import BuyerPersonaEngine
from revenue_engine.catalog import default_service_catalog, default_service_rules
from revenue_engine.matching.engine import ServiceMatchingEngine
from revenue_engine.models.types import BuyerPersona, ProjectSize, ServiceDefinition, ServiceMatch
from revenue_engine.pricing.engine import RevenueEstimator
from revenue_engine.prioritization.engine import SalesPrioritizationEngine
from tests.revenue_engine.test_revenue_pipeline import make_input


def test_default_catalog_includes_required_services() -> None:
    keys = {service.service_key for service in default_service_catalog()}
    assert {
        "comai",
        "custom_ai_development",
        "ai_automation",
        "ai_agents",
        "custom_saas",
        "mobile_apps",
        "website_development",
        "shopify_development",
        "woocommerce_development",
        "crm_development",
        "erp_development",
        "api_integration",
        "ui_ux",
    }.issubset(keys)
    assert default_service_rules()


def test_matching_engine_scores_term_and_pain_hits() -> None:
    item = make_input(
        pains=[{"category": "ecommerce", "value": "checkout friction", "confidence": 80.0}],
        technology_stack=["Shopify"],
        industry="ecommerce",
        narrative="Shopify storefront conversion issues.",
    )
    matches = ServiceMatchingEngine().match(item)
    assert matches
    assert matches[0].confidence >= matches[-1].confidence
    assert any(match.service.service_key == "shopify_development" for match in matches[:3])


def test_buyer_persona_engine_returns_canonical_personas() -> None:
    item = make_input()
    primary = ServiceMatch(
        service=default_service_catalog()[2],
        confidence=80.0,
        reasoning="test",
    )
    personas = BuyerPersonaEngine().infer(item, primary)
    allowed = {persona.value for persona in BuyerPersona}
    assert personas
    assert all(persona.persona in allowed for persona in personas)


def test_estimator_returns_range_labels() -> None:
    item = make_input()
    primary = ServiceMatch(
        service=ServiceDefinition(
            service_key="custom_saas",
            name="Custom SaaS",
            category="software",
            base_price=40000.0,
            monthly_price=3000.0,
            complexity="high",
        ),
        confidence=80.0,
        reasoning="test",
    )
    estimate = RevenueEstimator().estimate(item, primary)
    assert estimate.project_size in set(ProjectSize)
    prediction = SalesPrioritizationEngine().prioritize(item, primary, estimate)
    assert prediction.priority_level
    assert prediction.expected_sales_cycle_days > 0
