from datetime import UTC, datetime

from intelligence.entity_resolution import fuzzy_similarity, normalize_company_name, normalize_domain
from intelligence.entity_resolution.engine import EntityResolutionEngine
from intelligence.types import RawSignal


def test_normalization_and_fuzzy_matching() -> None:
    assert normalize_company_name("Nike, Inc.") == "nike"
    assert normalize_domain("https://www.nike.com/jobs") == "nike.com"
    assert fuzzy_similarity("Nike Incorporated", "Nike") >= 0.9


def test_entity_resolution_prefers_known_domain() -> None:
    signal = RawSignal(
        source="rss",
        url="https://nike.com/news/support-hiring",
        title="Nike is hiring support leaders",
        content="Nike is expanding customer support and adopting Zendesk.",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
    )

    result = EntityResolutionEngine().resolve(
        signal,
        known_domains={"nike.com": "Nike"},
    )

    assert result.company is not None
    assert result.company.value == "Nike"
    assert result.domain is not None
    assert result.domain.normalized_value == "nike.com"
    assert [technology.value for technology in result.technologies] == ["zendesk"]


def test_entity_resolution_skips_platform_domain_inference() -> None:
    signal = RawSignal(
        source="github_trending",
        url="https://github.com/acme-labs/ops-bot",
        title="GitHub: acme-labs/ops-bot",
        content="Automation helpers for SaaS ops teams.",
        published_at=datetime(2026, 7, 10, tzinfo=UTC),
        metadata={"owner": "acme-labs", "company_hints": ["acme-labs", "ops-bot"]},
    )

    result = EntityResolutionEngine().resolve(signal)

    assert result.company is not None
    assert result.company.value == "acme-labs"
    assert result.company.evidence["method"] in {"pattern_extraction", "alias_match"}
    assert result.domain is not None
    assert result.domain.normalized_value == "github.com"
    assert result.domain.evidence["method"] == "platform_domain"
