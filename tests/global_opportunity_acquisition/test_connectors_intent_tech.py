import pytest

from global_opportunity_acquisition.connectors.catalog import connector_catalog
from global_opportunity_acquisition.connectors.registry import ConnectorHealthEngine, ConnectorRegistry
from global_opportunity_acquisition.models.types import ConnectorStatus, OpportunityIntent
from global_opportunity_acquisition.intent_detection.engine import IntentDetectionEngine, INTENT_PATTERNS
from global_opportunity_acquisition.technology_detection.engine import TechnologyDetectionEngine, TECH_CATALOG


def test_catalog_has_current_and_new_sources() -> None:
    ids = {c.connector_id for c in connector_catalog()}
    for required in [
        "reddit",
        "rss",
        "hacker_news",
        "product_hunt",
        "github",
        "devto",
        "indie_hackers",
        "sec",
        "linkedin_jobs_public",
        "google_jobs",
        "techcrunch",
        "crunchbase",
        "g2",
        "capterra",
        "shopify_ecosystem",
        "public_procurement",
        "career_pages",
    ]:
        assert required in ids


def test_crunchbase_pending_credentials() -> None:
    c = next(x for x in connector_catalog() if x.connector_id == "crunchbase")
    assert c.status == ConnectorStatus.PENDING_CREDENTIALS
    assert c.requires_license is True


def test_all_connectors_respect_robots() -> None:
    assert all(c.respects_robots_txt and c.public_information_only for c in connector_catalog())


def test_registry_active_excludes_disabled() -> None:
    active = {c.connector_id for c in ConnectorRegistry().active()}
    assert "reddit" in active
    assert "crunchbase" not in active


def test_connector_metrics_fields() -> None:
    d = ConnectorRegistry().get("reddit")
    assert d is not None
    m = ConnectorHealthEngine().score(d, signals=3, companies=2, opportunities=2, duplicates=1, latency_ms=12.5)
    for field in [
        "connector_id",
        "connector_name",
        "health",
        "availability",
        "signals_found",
        "companies_found",
        "opportunities_found",
        "duplicates",
        "latency_ms",
        "errors",
        "quality_score",
        "trust_score",
        "coverage_score",
        "freshness_score",
        "roi_score",
    ]:
        assert hasattr(m, field)


@pytest.mark.parametrize("intent,_patterns,_conf", INTENT_PATTERNS)
def test_each_intent_detectable(intent: OpportunityIntent, _patterns: tuple[str, ...], _conf: float) -> None:
    sample = _patterns[0]
    hits = IntentDetectionEngine().detect([sample])
    assert any(h.intent == intent for h in hits)


@pytest.mark.parametrize("name,category,patterns", TECH_CATALOG)
def test_each_technology_detectable(name: str, category: str, patterns: tuple[str, ...]) -> None:
    hits = TechnologyDetectionEngine().detect([patterns[0]])
    assert any(h.technology == name and h.category == category for h in hits)
