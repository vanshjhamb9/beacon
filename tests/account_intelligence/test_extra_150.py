from uuid import uuid4

import pytest

from account_intelligence import AccountIntelligencePipeline
from account_intelligence.models.types import AccountIntelligenceInput, ObservedContact
from account_intelligence.technology_enrichment.engine import (
    AIStackEngine,
    CloudStackEngine,
    CRMDetectionEngine,
    MarketingStackEngine,
    SecurityStackEngine,
    TechnologyEnrichmentEngine,
)
from account_intelligence.confidence_engine.fields import field


@pytest.mark.parametrize(
    "hints",
    [
        ["salesforce"],
        ["hubspot", "mailchimp"],
        ["okta", "auth0"],
        ["aws", "cloudflare"],
        ["openai", "langchain"],
    ],
)
def test_stack_detectors(hints: list[str]) -> None:
    tech = TechnologyEnrichmentEngine().enrich(AccountIntelligenceInput(company_name="X", html_hints=hints, tech_hints=hints))
    assert CRMDetectionEngine().detect(tech) or MarketingStackEngine().detect(tech) or SecurityStackEngine().detect(tech) or CloudStackEngine().detect(tech) or AIStackEngine().detect(tech)


@pytest.mark.parametrize("conf", [0, 25, 50, 75, 100])
def test_field_helper_bounds(conf: int) -> None:
    fv = field("x", confidence=float(conf), source="t")
    assert 0 <= fv.confidence <= 100
    assert fv.last_verified is not None


def test_field_helper_missing() -> None:
    fv = field(None, confidence=90, source="t")
    assert fv.value is None
    assert fv.confidence == 0
    assert "never_fabricate:true" in fv.evidence


@pytest.mark.parametrize("i", range(30))
def test_batch_deterministic_keys(i: int) -> None:
    item = AccountIntelligenceInput(
        company_id=uuid4(),
        company_name=f"Batch {i}",
        domain=f"batch{i}.io",
        html_hints=["react", "https"],
        observed_contacts=[
            ObservedContact(full_name=f"P{i}", role="CEO", business_email=f"p{i}@batch{i}.io", source="s", evidence=[])
        ]
        if i % 2 == 0
        else [],
    )
    a = AccountIntelligencePipeline().process(item)
    b = AccountIntelligencePipeline().process(item)
    assert a.relationship_graph.company_key == b.relationship_graph.company_key
    assert a.ai_readiness.overall == b.ai_readiness.overall
