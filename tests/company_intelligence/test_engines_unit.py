"""CIR engine-level unit coverage for volume + edge cases."""

from __future__ import annotations

import pytest

from company_intelligence.buying_signals.engine import BuyingSignalEngine
from company_intelligence.company_understanding.engine import CompanyUnderstandingEngine
from company_intelligence.contact_recovery.engine import ContactRecoveryEngine
from company_intelligence.icp_detection.engine import IcpDetectionEngine
from company_intelligence.models.types import WebsiteCorpus, WebsitePage
from company_intelligence.opportunity_narrative.engine import OpportunityNarrativeEngine
from company_intelligence.product_intelligence.engine import ProductIntelligenceEngine
from company_intelligence.revenue_readiness.engine import RevenueReadinessEngine, WEIGHTS
from company_intelligence.service_match.engine import ServiceMatchEngineV3, URBAN_WEBWORKS_SERVICES
from company_intelligence.technology_intelligence.engine import TechnologyIntelligenceEngine
from company_intelligence.website_understanding.engine import MAX_PAGES, PAGE_PATHS, WebsiteUnderstandingEngine


def _corpus(text: str, *, path: str = "/") -> WebsiteCorpus:
    return WebsiteCorpus(
        website="https://x.test",
        domain="x.test",
        pages=[
            WebsitePage(
                url=f"https://x.test{path}",
                path=path,
                title="X",
                description="SaaS platform",
                headings=["Product"],
                text=text,
            )
        ],
        page_count=1,
        crawled=True,
    )


@pytest.mark.parametrize("path", list(PAGE_PATHS))
def test_page_paths_declared(path):
    assert isinstance(path, str)


def test_max_pages_25():
    assert MAX_PAGES == 25


@pytest.mark.parametrize("i", range(120))
def test_website_preloaded_pages(i):
    engine = WebsiteUnderstandingEngine()
    corpus = engine.collect(
        {
            "website": f"https://site{i}.test",
            "domain": f"site{i}.test",
            "website_pages": [
                {
                    "url": f"https://site{i}.test",
                    "path": "/",
                    "title": f"Site{i}",
                    "text": f"hello automation saas enterprise api site{i}",
                }
            ],
        }
    )
    assert corpus.crawled
    assert corpus.page_count == 1


@pytest.mark.parametrize("i", range(80))
def test_company_understanding_industry_variants(i):
    industries = (
        "saas software platform",
        "healthcare clinic hospital",
        "fintech banking payments",
        "ecommerce shopify retail",
        "education school university",
        "manufacturing factory industrial",
        "real estate property",
        "marketing agency advertising",
    )
    blob = industries[i % len(industries)]
    profile = CompanyUnderstandingEngine().extract(_corpus(blob), {"company_name": f"Co{i}"})
    assert profile.industry.value != "UNKNOWN" or profile.description.value == "UNKNOWN"


@pytest.mark.parametrize("i", range(60))
def test_product_intelligence_pricing(i):
    catalog = ProductIntelligenceEngine().extract(
        _corpus("starter pro enterprise free trial pricing api marketplace", path="/pricing")
    )
    assert catalog.pricing.value != "UNKNOWN" or catalog.free_trial.value == "Yes" or catalog.plans


@pytest.mark.parametrize("i", range(50))
def test_icp_engine(i):
    texts = (
        "built for enterprise fortune 500",
        "perfect for smb small business",
        "hospitals and clinics healthcare organizations",
        "banks and financial institutions",
        "schools and universities educators",
        "developers and engineering teams api-first",
    )
    icp = IcpDetectionEngine().detect(_corpus(texts[i % len(texts)]))
    assert icp.primary_icp.value != "UNKNOWN"


@pytest.mark.parametrize("i", range(40))
def test_tech_engine(i):
    texts = (
        "wp-content wordpress",
        "gtag( googletagmanager",
        "js.stripe stripe.com",
        "hubspot hs-scripts",
        "amazonaws.com aws",
        "openai gpt-4",
    )
    hits = TechnologyIntelligenceEngine().detect(_corpus(texts[i % len(texts)]))
    assert hits


@pytest.mark.parametrize("i", range(40))
def test_signal_engine(i):
    texts = (
        "we're hiring now",
        "series a raised funding",
        "product launch now available",
        "soc 2 security compliance",
        "new integration with slack",
    )
    signals = BuyingSignalEngine().detect(_corpus(texts[i % len(texts)]))
    assert signals


@pytest.mark.parametrize("i", range(30))
def test_service_match_engine(i):
    from company_intelligence.models.types import CompanyBusinessProfile, IcpProfile, ProductCatalog, AttributedValue

    business = CompanyBusinessProfile(
        description=AttributedValue(value="enterprise saas automation ai agents", confidence=80, source="t"),
        industry=AttributedValue(value="Software", confidence=80, source="t"),
        primary_product=AttributedValue(value="Automation Platform", confidence=80, source="t"),
    )
    matches = ServiceMatchEngineV3().match(
        corpus=_corpus("enterprise saas automation ai agents api integrations aws"),
        business=business,
        products=ProductCatalog(),
        icp=IcpProfile(primary_icp=AttributedValue(value="Enterprise", confidence=80, source="t")),
        technologies=[],
        signals=[],
    )
    assert matches
    assert matches[0].service in {s["service"] for s in URBAN_WEBWORKS_SERVICES}


@pytest.mark.parametrize("i", range(20))
def test_contact_recovery(i):
    people = ContactRecoveryEngine().recover(
        _corpus(f"Ada Example{i}, CEO. hello@firm{i}.test", path="/team"),
        {"decision_makers": [{"name": f"Pat {i}", "role": "CTO", "email": f"pat{i}@firm.test"}]},
    )
    assert people
    assert all(p.evidence for p in people)


@pytest.mark.parametrize("i", range(20))
def test_narrative_engine(i):
    from company_intelligence.models.types import (
        AttributedValue,
        BuyingSignal,
        CompanyBusinessProfile,
        IcpProfile,
        ServiceMatch,
    )

    narrative = OpportunityNarrativeEngine().build(
        company_name=f"Co{i}",
        business=CompanyBusinessProfile(
            industry=AttributedValue(value="Software", confidence=80, source="t"),
            primary_product=AttributedValue(value="Ops Platform", confidence=80, source="t"),
        ),
        icp=IcpProfile(primary_icp=AttributedValue(value="Enterprise", confidence=80, source="t")),
        signals=[BuyingSignal(signal_type="Hiring", confidence=80, excerpt="hiring")],
        matches=[
            ServiceMatch(
                service="AI Automation",
                need_score=80,
                confidence=80,
                reason="fit",
                potential_value="$40k",
                evidence=["x"],
            )
        ],
    )
    assert "Co" in narrative.why_this_company
    assert narrative.which_service == "AI Automation"


def test_weights_sum_100():
    assert abs(sum(WEIGHTS.values()) - 100.0) < 0.01


@pytest.mark.parametrize("total,expected", [(0, "Rejected"), (40, "Observed"), (60, "Promising"), (75, "Revenue Ready"), (90, "Priority Account")])
def test_classification_bands(total, expected):
    engine = RevenueReadinessEngine()
    assert engine._classify(total).value == expected
