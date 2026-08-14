from __future__ import annotations

from datetime import UTC, datetime, timedelta

from live_opportunity_discovery.buying_signal_classifier import BuyingSignalClassifier
from live_opportunity_discovery.company_expansion import CompanyExpansion
from live_opportunity_discovery.company_resolver import CompanyResolver
from live_opportunity_discovery.discovery_router import DiscoveryRouter
from live_opportunity_discovery.duplicate_detector import DuplicateDetector
from live_opportunity_discovery.freshness_filter import FreshnessFilter
from live_opportunity_discovery.intent_classifier import IntentClassifier
from live_opportunity_discovery.priority_ranker import PriorityInput, PriorityRanker
from live_opportunity_discovery.source_registry import SourceRegistry


NOW = datetime(2026, 7, 29, tzinfo=UTC)


def event_payload(headline: str = "OpenAI hiring recruiters in Singapore") -> dict[str, object]:
    return {
        "company_name": "Open AI Inc.",
        "headline": headline,
        "description": "The company is expanding its team and hiring talent acquisition roles.",
        "source": "Company Careers",
        "url": "https://example.com/jobs",
        "event_timestamp": NOW - timedelta(days=2),
        "company_size": 900,
        "funding_amount": 100_000_000,
        "has_decision_maker": True,
        "revenue_potential": 95,
        "competition": 20,
    }


def test_discovery_router_requires_evidence_and_normalizes_event() -> None:
    event = DiscoveryRouter().normalize(event_payload())
    assert event.company_name == "Open AI Inc."
    assert len(event.evidence) == 1
    assert event.evidence[0].source == "Company Careers"


def test_buying_signal_classifier_discards_unknown_and_classifies_known() -> None:
    classifier = BuyingSignalClassifier()
    known = classifier.classify(DiscoveryRouter().normalize(event_payload()))
    unknown = classifier.classify(
        DiscoveryRouter().normalize({**event_payload("Company celebrates anniversary"), "description": ""})
    )
    assert known is not None
    assert known.category == "HIRING"
    assert known.event_type == "Hiring Recruiters"
    assert unknown is None


def test_freshness_filter_accepts_21_days_and_rejects_older() -> None:
    freshness = FreshnessFilter()
    assert freshness.evaluate(NOW - timedelta(days=3), now=NOW).bucket == "priority"
    assert freshness.evaluate(NOW - timedelta(days=7), now=NOW).bucket == "preferred"
    assert freshness.evaluate(NOW - timedelta(days=21), now=NOW).accepted is True
    assert freshness.evaluate(NOW - timedelta(days=22), now=NOW).accepted is False


def test_company_resolver_collapses_name_variants() -> None:
    resolver = CompanyResolver()
    assert resolver.normalize("Open AI") == resolver.normalize("OPENAI Inc.")
    assert resolver.normalize("openai") == "openai"


def test_duplicate_detector_merges_evidence_for_same_event() -> None:
    router = DiscoveryRouter()
    first = router.normalize(event_payload())
    second = router.normalize(
        {
            **event_payload(),
            "source": "Google News",
            "url": "https://news.example.com/openai-hiring",
            "evidence": [
                {
                    "source": "Google News",
                    "url": "https://news.example.com/openai-hiring",
                    "discovered_at": NOW,
                    "headline": "OpenAI hiring recruiters",
                    "confidence": 90,
                }
            ],
        }
    )
    detector = DuplicateDetector()
    fingerprint = detector.fingerprint(first, category="HIRING", event_type="Hiring Recruiters")
    merged = detector.merge([first, second], category="HIRING", event_type="Hiring Recruiters")
    assert fingerprint.normalized_company == "openai"
    assert len(merged.evidence) == 2


def test_company_expansion_and_intent_classifier_generate_multiple_services() -> None:
    needs = CompanyExpansion().expand("New office", "EXPANSION")
    services = IntentClassifier().classify("New office", "EXPANSION", " ".join(needs))
    assert "Need recruitment" in needs
    assert "Recruitment Automation" in services
    assert "Sales Automation" in services


def test_priority_ranker_uses_weighted_buying_event_factors() -> None:
    score = PriorityRanker().score(
        PriorityInput(
            buying_intent=94,
            freshness=100,
            company_size=88,
            funding=100,
            evidence_count=4,
            source_quality=93,
            decision_maker=100,
            revenue_potential=95,
            competition=20,
            service_match=90,
        )
    )
    assert score.score >= 85
    assert score.priority == "P0"
    assert score.breakdown["buying_intent"] > score.breakdown["competition"]


def test_source_registry_weights_are_configurable() -> None:
    registry = SourceRegistry()
    assert registry.weight_for("Official Company News") == 100
    assert registry.weight_for("RSS") == 65
    assert registry.weight_for("Unknown Source") == 50
