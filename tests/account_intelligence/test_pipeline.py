from datetime import UTC, datetime
from uuid import uuid4

from account_intelligence import (
    SCORING_VERSION,
    AccountIntelligenceInput,
    AccountIntelligencePipeline,
    AccountIntelligenceService,
    SalesReadinessCategory,
)
from account_intelligence.models.types import ObservedContact


def _item(**overrides: object) -> AccountIntelligenceInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Northstar Labs",
        "website": "https://northstar.io",
        "domain": "northstar.io",
        "industry": "SaaS",
        "country": "US",
        "city": "Austin",
        "employee_count": 80,
        "funding": "Series A",
        "latest_funding_round": "series_a",
        "hiring_trend": 40.0,
        "expansion_score": 55.0,
        "buying_intent": 70.0,
        "html_hints": [
            "react",
            "next.js",
            "https",
            "viewport",
            "stripe",
            "hubspot",
            "schema.org",
            "careers",
            "pricing",
            "contact",
        ],
        "tech_hints": ["aws", "postgres", "openai"],
        "observed_contacts": [
            ObservedContact(
                full_name="Alex Founder",
                role="CEO",
                business_email="alex@northstar.io",
                linkedin_url="https://linkedin.com/in/alex",
                source="public_linkedin",
                evidence=["public:true"],
            ),
            ObservedContact(
                full_name="Sam Tech",
                role="CTO",
                business_email="sam@northstar.io",
                source="company_about",
                evidence=["about_page:true"],
            ),
        ],
        "campaigns": ["Q3 outbound"],
        "meetings": ["Discovery"],
        "now": datetime.now(UTC),
    }
    payload.update(overrides)
    return AccountIntelligenceInput.model_validate(payload)


def test_scoring_version() -> None:
    assert SCORING_VERSION == "aip-v1"


def test_pipeline_deterministic() -> None:
    item = _item()
    a = AccountIntelligencePipeline().process(item)
    b = AccountIntelligencePipeline().process(item)
    assert a.sales_readiness.score == b.sales_readiness.score
    assert a.relationship_graph.company_key == b.relationship_graph.company_key
    assert a.confidence.overall == b.confidence.overall
    assert [m.full_name for m in a.buying_committee] == [m.full_name for m in b.buying_committee]


def test_pipeline_evidence_and_no_fabrication() -> None:
    d = AccountIntelligencePipeline().process(_item())
    assert "compose_only:true" in d.evidence_chain
    assert "never_fabricate:true" in d.evidence_chain
    assert "no_gpt:true" in d.evidence_chain
    assert all(m.fabricated is False for m in d.buying_committee)
    assert "apollo" in d.licensed_providers_disabled


def test_service_evaluate_many() -> None:
    out = AccountIntelligenceService().evaluate_many([_item(company_name=f"C{i}") for i in range(3)])
    assert len(out) == 3


def test_sales_readiness_categories_present() -> None:
    d = AccountIntelligencePipeline().process(_item())
    assert isinstance(d.sales_readiness.category, SalesReadinessCategory)
    assert 0 <= d.sales_readiness.score <= 100


def test_field_attribution() -> None:
    d = AccountIntelligencePipeline().process(_item())
    assert d.profile.company_name.confidence > 0
    assert d.profile.company_name.source
    assert d.profile.company_name.last_verified is not None
    assert d.profile.revenue_estimate.value is None  # never invented
    assert d.profile.revenue_estimate.confidence == 0
