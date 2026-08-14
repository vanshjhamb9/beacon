"""Additional tests for signal normalizer — comprehensive edge cases."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from opportunity_connector_platform.connector_events import EvidenceEvent
from opportunity_connector_platform.signal_normalizer import (
    COUNTRY_ALIASES,
    LANGUAGE_ALIASES,
    SignalNormalizer,
)


def _make_event(**overrides: object) -> EvidenceEvent:
    now = datetime.now(UTC)
    defaults = dict(
        connector_id="c", connector_version="1.0", headline="h",
        event_type="Hiring", event_category="Identity",
        published_at=now, captured_at=now, evidence="e", collector="t",
    )
    defaults.update(overrides)
    return EvidenceEvent(**defaults)


class TestCountryEdgeCases:
    def test_usa_uppercase(self):
        n = SignalNormalizer()
        assert n.country("USA") == "US"

    def test_uk_uppercase(self):
        n = SignalNormalizer()
        assert n.country("UK") == "GB"

    def test_two_letter_any(self):
        n = SignalNormalizer()
        assert n.country("JP") == "JP"

    def test_long_name_kept(self):
        n = SignalNormalizer()
        assert n.country("United States of America") == "US"

    def test_mixed_case_alias(self):
        n = SignalNormalizer()
        assert n.country("UnItEd StAtEs") == "US"

    def test_three_letter_code(self):
        n = SignalNormalizer()
        assert n.country("USA") == "US"

    def test_germany_alias(self):
        n = SignalNormalizer()
        assert n.country("Germany") == "DE"

    def test_france_alias(self):
        n = SignalNormalizer()
        assert n.country("France") == "FR"


class TestLanguageEdgeCases:
    def test_english_lowercase(self):
        n = SignalNormalizer()
        assert n.language("english") == "en"

    def test_english_mixed_case(self):
        n = SignalNormalizer()
        assert n.language("English") == "en"

    def test_en_us_mixed(self):
        n = SignalNormalizer()
        assert n.language("en-US") == "en"

    def test_unknown_passthrough(self):
        n = SignalNormalizer()
        assert n.language("unknown") == "unknown"

    def test_custom_language(self):
        n = SignalNormalizer()
        assert n.language("esperanto") == "esperanto"

    def test_chinese(self):
        n = SignalNormalizer()
        assert n.language("chinese") == "zh"

    def test_japanese(self):
        n = SignalNormalizer()
        assert n.language("japanese") == "ja"

    def test_korean(self):
        n = SignalNormalizer()
        assert n.language("korean") == "ko"

    def test_hindi(self):
        n = SignalNormalizer()
        assert n.language("hindi") == "hi"

    def test_arabic(self):
        n = SignalNormalizer()
        assert n.language("arabic") == "ar"


class TestCompanyEdgeCases:
    def test_only_whitespace(self):
        n = SignalNormalizer()
        result = n.company("   ")
        assert result == ""

    def test_mixed_suffixes(self):
        n = SignalNormalizer()
        result = n.company("Acme Inc.")
        assert "Inc" not in result

    def test_ag_suffix(self):
        n = SignalNormalizer()
        result = n.company("Siemens AG")
        assert "AG" not in result

    def test_sas_suffix(self):
        n = SignalNormalizer()
        result = n.company("Dassault SAS")
        assert "SAS" not in result

    def test_pty_suffix(self):
        n = SignalNormalizer()
        result = n.company("Atlassian Pty Ltd")
        assert "Pty" not in result or "Ltd" not in result

    def test_co_suffix(self):
        n = SignalNormalizer()
        result = n.company("Acme Co")
        assert result.strip() != "Acme Co"

    def test_no_suffix(self):
        n = SignalNormalizer()
        assert n.company("Google") == "Google"

    def test_single_space(self):
        n = SignalNormalizer()
        assert n.company("Acme Corp") == "Acme"

    def test_multiple_spaces(self):
        n = SignalNormalizer()
        assert n.company("Acme    Corp") == "Acme"

    def test_leading_trailing_spaces(self):
        n = SignalNormalizer()
        assert n.company("  Acme  ") == "Acme"


class TestUrlEdgeCases:
    def test_http_prefix(self):
        n = SignalNormalizer()
        assert n.url("http://example.com") == "example.com"

    def test_https_prefix(self):
        n = SignalNormalizer()
        assert n.url("https://example.com") == "example.com"

    def test_www_prefix(self):
        n = SignalNormalizer()
        assert n.url("www.example.com") == "example.com"

    def test_trailing_slash(self):
        n = SignalNormalizer()
        assert n.url("example.com/") == "example.com"

    def test_complex_path(self):
        n = SignalNormalizer()
        assert n.url("https://example.com/path/to/page") == "example.com/path/to/page"

    def test_with_query(self):
        n = SignalNormalizer()
        assert n.url("https://example.com/page?q=1") == "example.com/page?q=1"

    def test_with_fragment(self):
        n = SignalNormalizer()
        assert n.url("https://example.com/page#section") == "example.com/page#section"

    def test_none(self):
        n = SignalNormalizer()
        assert n.url(None) is None

    def test_empty_string(self):
        n = SignalNormalizer()
        result = n.url("")
        assert result is None or result == ""


class TestFullNormalizeEdgeCases:
    def test_naive_datetime_converted(self):
        n = SignalNormalizer()
        naive = datetime(2025, 6, 15, 10, 30, 0)
        event = _make_event(published_at=naive, captured_at=naive)
        result = n.normalize(event)
        assert result.published_at.tzinfo is not None
        assert result.captured_at.tzinfo is not None

    def test_aware_datetime_preserved(self):
        n = SignalNormalizer()
        aware = datetime(2025, 6, 15, 10, 30, 0, tzinfo=ZoneInfo("US/Eastern"))
        event = _make_event(published_at=aware, captured_at=aware)
        result = n.normalize(event)
        assert result.published_at.tzinfo is not None

    def test_country_normalized(self):
        n = SignalNormalizer()
        event = _make_event(country="uk")
        result = n.normalize(event)
        assert result.country == "GB"

    def test_language_normalized(self):
        n = SignalNormalizer()
        event = _make_event(language="french")
        result = n.normalize(event)
        assert result.language == "fr"

    def test_company_stripped(self):
        n = SignalNormalizer()
        event = _make_event(company_name="  Acme   Corp  ")
        result = n.normalize(event)
        assert result.company_name == "Acme"

    def test_headline_cleaned(self):
        n = SignalNormalizer()
        event = _make_event(headline="  Acme   is   hiring  ")
        result = n.normalize(event)
        assert result.headline == "Acme is hiring"

    def test_summary_cleaned(self):
        n = SignalNormalizer()
        event = _make_event(summary="  Big   news   today  ")
        result = n.normalize(event)
        assert result.summary == "Big news today"

    def test_url_normalized(self):
        n = SignalNormalizer()
        event = _make_event(url="https://example.com/news")
        result = n.normalize(event)
        assert result.url == "example.com/news"

    def test_preserves_event_type(self):
        n = SignalNormalizer()
        event = _make_event(event_type="Funding")
        result = n.normalize(event)
        assert result.event_type == "Funding"

    def test_preserves_connector_id(self):
        n = SignalNormalizer()
        event = _make_event(connector_id="linkedin")
        result = n.normalize(event)
        assert result.connector_id == "linkedin"

    def test_preserves_confidence(self):
        n = SignalNormalizer()
        event = _make_event(confidence=87.5)
        result = n.normalize(event)
        assert result.confidence == 87.5

    def test_preserves_evidence(self):
        n = SignalNormalizer()
        event = _make_event(evidence="Test evidence text")
        result = n.normalize(event)
        assert result.evidence == "Test evidence text"

    def test_preserves_raw_metadata(self):
        n = SignalNormalizer()
        meta = {"key": "value"}
        event = _make_event(raw_metadata=meta)
        result = n.normalize(event)
        assert result.raw_metadata == meta
