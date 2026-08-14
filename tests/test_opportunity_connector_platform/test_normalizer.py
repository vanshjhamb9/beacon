"""Tests for signal normalizer."""

from __future__ import annotations

from datetime import UTC, datetime

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
        connector_id="test",
        connector_version="1.0",
        company_name="Acme Corp",
        headline="Acme hiring engineers",
        summary="Acme is expanding",
        event_type="Hiring",
        event_category="Identity",
        url="https://example.com/news/1",
        published_at=now,
        captured_at=now,
        country="US",
        language="en",
        confidence=85.0,
        evidence="Acme Corp is hiring",
        collector="test",
    )
    defaults.update(overrides)
    return EvidenceEvent(**defaults)


class TestCountryNormalization:
    def test_usa_to_us(self):
        n = SignalNormalizer()
        assert n.country("usa") == "US"

    def test_united_states_to_us(self):
        n = SignalNormalizer()
        assert n.country("united states") == "US"

    def test_uk_to_gb(self):
        n = SignalNormalizer()
        assert n.country("uk") == "GB"

    def test_united_kingdom_to_gb(self):
        n = SignalNormalizer()
        assert n.country("united kingdom") == "GB"

    def test_india(self):
        n = SignalNormalizer()
        assert n.country("india") == "IN"

    def test_germany(self):
        n = SignalNormalizer()
        assert n.country("germany") == "DE"

    def test_france(self):
        n = SignalNormalizer()
        assert n.country("france") == "FR"

    def test_canada(self):
        n = SignalNormalizer()
        assert n.country("canada") == "CA"

    def test_australia(self):
        n = SignalNormalizer()
        assert n.country("australia") == "AU"

    def test_japan(self):
        n = SignalNormalizer()
        assert n.country("japan") == "JP"

    def test_china(self):
        n = SignalNormalizer()
        assert n.country("china") == "CN"

    def test_brazil(self):
        n = SignalNormalizer()
        assert n.country("brazil") == "BR"

    def test_two_letter_code(self):
        n = SignalNormalizer()
        assert n.country("DE") == "DE"

    def test_two_letter_lowercase(self):
        n = SignalNormalizer()
        assert n.country("de") == "DE"

    def test_none_returns_none(self):
        n = SignalNormalizer()
        assert n.country(None) is None

    def test_empty_returns_none(self):
        n = SignalNormalizer()
        assert n.country("") is None

    def test_unknown_country_kept(self):
        n = SignalNormalizer()
        assert n.country("Atlantis") == "Atlantis"

    def test_whitespace_stripped(self):
        n = SignalNormalizer()
        assert n.country("  US  ") == "US"

    def test_singapore(self):
        n = SignalNormalizer()
        assert n.country("singapore") == "SG"

    def test_israel(self):
        n = SignalNormalizer()
        assert n.country("israel") == "IL"

    def test_ireland(self):
        n = SignalNormalizer()
        assert n.country("ireland") == "IE"

    def test_spain(self):
        n = SignalNormalizer()
        assert n.country("spain") == "ES"

    def test_italy(self):
        n = SignalNormalizer()
        assert n.country("italy") == "IT"

    def test_south_korea(self):
        n = SignalNormalizer()
        assert n.country("south korea") == "KR"

    def test_netherlands(self):
        n = SignalNormalizer()
        assert n.country("netherlands") == "NL"

    def test_sweden(self):
        n = SignalNormalizer()
        assert n.country("sweden") == "SE"

    def test_switzerland(self):
        n = SignalNormalizer()
        assert n.country("switzerland") == "CH"


class TestLanguageNormalization:
    def test_english(self):
        n = SignalNormalizer()
        assert n.language("english") == "en"

    def test_en_us(self):
        n = SignalNormalizer()
        assert n.language("en-us") == "en"

    def test_en_gb(self):
        n = SignalNormalizer()
        assert n.language("en-gb") == "en"

    def test_spanish(self):
        n = SignalNormalizer()
        assert n.language("spanish") == "es"

    def test_french(self):
        n = SignalNormalizer()
        assert n.language("french") == "fr"

    def test_german(self):
        n = SignalNormalizer()
        assert n.language("german") == "de"

    def test_unknown_default(self):
        n = SignalNormalizer()
        assert n.language(None) == "unknown"

    def test_empty_default(self):
        n = SignalNormalizer()
        assert n.language("") == "unknown"

    def test_passthrough(self):
        n = SignalNormalizer()
        assert n.language("en") == "en"

    def test_lowercase(self):
        n = SignalNormalizer()
        assert n.language("EN") == "en"

    def test_whitespace_stripped(self):
        n = SignalNormalizer()
        assert n.language("  fr  ") == "fr"


class TestCompanyNormalization:
    def test_whitespace_collapsed(self):
        n = SignalNormalizer()
        assert n.company("  Acme   Corp  ") == "Acme"

    def test_inc_removed(self):
        n = SignalNormalizer()
        result = n.company("Acme Inc.")
        assert "Inc" not in result

    def test_llc_removed(self):
        n = SignalNormalizer()
        result = n.company("Acme LLC")
        assert "LLC" not in result

    def test_ltd_removed(self):
        n = SignalNormalizer()
        result = n.company("Acme Ltd")
        assert "Ltd" not in result

    def test_corp_removed(self):
        n = SignalNormalizer()
        result = n.company("Acme Corp")
        assert "Corp" not in result

    def test_gmbh_removed(self):
        n = SignalNormalizer()
        result = n.company("Acme GmbH")
        assert "GmbH" not in result

    def test_simple_name(self):
        n = SignalNormalizer()
        assert n.company("Acme") == "Acme"

    def test_empty_returns_original(self):
        n = SignalNormalizer()
        assert n.company("") == ""

    def test_only_whitespace(self):
        n = SignalNormalizer()
        result = n.company("   ")
        assert result == "" or result == "   "

    def test_company_without_suffix(self):
        n = SignalNormalizer()
        assert n.company("  Acme Corp  ") == "Acme"

    def test_whitespace_collapsed_no_suffix(self):
        n = SignalNormalizer()
        assert n.company("  Acme   Tech  ") == "Acme Tech"


class TestUrlNormalization:
    def test_strip_http(self):
        n = SignalNormalizer()
        assert n.url("http://example.com") == "example.com"

    def test_strip_https(self):
        n = SignalNormalizer()
        assert n.url("https://example.com") == "example.com"

    def test_strip_www(self):
        n = SignalNormalizer()
        assert n.url("www.example.com") == "example.com"

    def test_strip_trailing_slash(self):
        n = SignalNormalizer()
        assert n.url("example.com/") == "example.com"

    def test_none_returns_none(self):
        n = SignalNormalizer()
        assert n.url(None) is None

    def test_complex_url(self):
        n = SignalNormalizer()
        assert n.url("https://www.example.com/path") == "example.com/path"


class TestFullNormalize:
    def test_normalizes_all_fields(self):
        n = SignalNormalizer()
        event = _make_event(
            company_name="  Acme   Tech  ",
            country="usa",
            language="english",
        )
        result = n.normalize(event)
        assert result.company_name == "Acme Tech"
        assert result.country == "US"
        assert result.language == "en"

    def test_preserves_unchanged_fields(self):
        n = SignalNormalizer()
        event = _make_event()
        result = n.normalize(event)
        assert result.connector_id == event.connector_id
        assert result.event_type == event.event_type
        assert result.confidence == event.confidence

    def test_headline_whitespace_collapsed(self):
        n = SignalNormalizer()
        event = _make_event(headline="  Acme   is   hiring  ")
        result = n.normalize(event)
        assert result.headline == "Acme is hiring"

    def test_summary_whitespace_collapsed(self):
        n = SignalNormalizer()
        event = _make_event(summary="  Acme   Corp   summary  ")
        result = n.normalize(event)
        assert result.summary == "Acme Corp summary"

    def test_utc_dates(self):
        n = SignalNormalizer()
        naive = datetime(2025, 1, 1, 12, 0, 0)
        event = _make_event(published_at=naive, captured_at=naive)
        result = n.normalize(event)
        assert result.published_at.tzinfo is not None
        assert result.captured_at.tzinfo is not None

    def test_country_normalized_in_event(self):
        n = SignalNormalizer()
        event = _make_event(country="uk")
        result = n.normalize(event)
        assert result.country == "GB"

    def test_language_normalized_in_event(self):
        n = SignalNormalizer()
        event = _make_event(language="english")
        result = n.normalize(event)
        assert result.language == "en"

    def test_company_suffixed_stripped(self):
        n = SignalNormalizer()
        event = _make_event(company_name="Acme Inc.")
        result = n.normalize(event)
        assert "Inc" not in (result.company_name or "")


class TestCountryAliases:
    def test_all_aliases_are_uppercase(self):
        for alias, code in COUNTRY_ALIASES.items():
            assert code == code.upper(), f"Alias {alias} maps to {code}"

    def test_usa_maps_to_us(self):
        assert COUNTRY_ALIASES["usa"] == "US"

    def test_uk_maps_to_gb(self):
        assert COUNTRY_ALIASES["uk"] == "GB"


class TestLanguageAliases:
    def test_english_maps_to_en(self):
        assert LANGUAGE_ALIASES["english"] == "en"

    def test_en_us_maps_to_en(self):
        assert LANGUAGE_ALIASES["en-us"] == "en"
