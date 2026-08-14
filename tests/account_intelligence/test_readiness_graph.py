from uuid import uuid4

from account_intelligence import AccountIntelligencePipeline, AccountIntelligenceService
from account_intelligence.models.types import AccountIntelligenceInput, ObservedContact, SalesReadinessCategory


def _rich(**overrides: object) -> AccountIntelligenceInput:
    base: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Ready Co",
        "domain": "ready.co",
        "website": "https://ready.co",
        "industry": "Fintech",
        "country": "US",
        "employee_count": 120,
        "funding": "Series B",
        "latest_funding_round": "series_b",
        "hiring_trend": 60,
        "expansion_score": 70,
        "buying_intent": 80,
        "html_hints": ["react", "https", "viewport", "hubspot", "stripe", "careers", "pricing", "chatbot"],
        "tech_hints": ["aws", "postgres"],
        "observed_contacts": [
            ObservedContact(
                full_name="Jordan Lee",
                role="CEO",
                business_email="jordan@ready.co",
                linkedin_url="https://linkedin.com/in/jordan",
                source="public",
                evidence=["e"],
            )
        ],
    }
    base.update(overrides)
    return AccountIntelligenceInput.model_validate(base)


def test_ai_readiness_dimensions() -> None:
    d = AccountIntelligencePipeline().process(_rich(html_hints=["https"]))  # weak site -> higher needs
    ai = d.ai_readiness
    for attr in [
        "need_ai_automation",
        "need_crm",
        "need_erp",
        "need_saas",
        "need_website",
        "need_mobile_app",
        "need_custom_software",
        "need_chatbot",
        "need_internal_ai",
        "need_analytics",
        "need_knowledge_base",
        "need_workflow_automation",
        "need_integrations",
        "overall",
    ]:
        assert 0 <= getattr(ai, attr) <= 100


def test_sales_readiness_bant_dimensions() -> None:
    d = AccountIntelligencePipeline().process(_rich())
    s = d.sales_readiness
    for attr in [
        "opportunity",
        "budget",
        "authority",
        "need",
        "timing",
        "data_completeness",
        "decision_makers",
        "contact_availability",
        "technology",
        "growth",
        "urgency",
        "score",
    ]:
        assert 0 <= getattr(s, attr) <= 100
    assert s.category in set(SalesReadinessCategory)


def test_relationship_graph_append_only() -> None:
    d = AccountIntelligencePipeline().process(_rich(campaigns=["C1"], emails=["e1"], replies=["r1"], proposals=["p1"], referrals=["ref"], history=["h1"]))
    types = {n.node_type for n in d.relationship_graph.nodes}
    assert "company" in types
    assert "decision_maker" in types
    assert d.relationship_graph.edges
    assert all("append_only:true" in n.evidence for n in d.relationship_graph.nodes)


def test_search_filters() -> None:
    svc = AccountIntelligenceService()
    decisions = [
        svc.evaluate(_rich(company_name="Alpha", industry="SaaS", country="US")),
        svc.evaluate(_rich(company_name="Beta Health", industry="Healthcare", country="UK", html_hints=["wordpress"])),
    ]
    assert len(svc.search(decisions, query="alpha")) == 1
    assert len(svc.search(decisions, filters={"industry": "Healthcare"})) == 1
    assert len(svc.search(decisions, filters={"country": "US"})) == 1
    assert len(svc.search(decisions, filters={"technology": "react"})) >= 1


def test_website_and_business_profiles() -> None:
    d = AccountIntelligencePipeline().process(_rich())
    assert d.website.ssl is True
    assert d.website.mobile is True
    assert d.business.growth_stage in {"startup", "early", "growth", "scale"}
    assert d.business.customer_segment in {"smb", "midmarket", "enterprise"}


def test_verification_history_and_confidence() -> None:
    d = AccountIntelligencePipeline().process(_rich())
    assert d.verification_history
    assert d.confidence.overall > 0
    assert d.confidence.field_scores
    assert d.timeline
