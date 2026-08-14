"""Deterministic evidence event normalization.

Countries, currencies, languages, dates, timezones, company names,
domains, job titles, technologies, industries — all become deterministic.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from opportunity_connector_platform.connector_events import EvidenceEvent

COUNTRY_ALIASES: dict[str, str] = {
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "india": "IN",
    "germany": "DE",
    "france": "FR",
    "canada": "CA",
    "australia": "AU",
    "japan": "JP",
    "china": "CN",
    "brazil": "BR",
    "netherlands": "NL",
    "sweden": "SE",
    "switzerland": "CH",
    "singapore": "SG",
    "israel": "IL",
    "ireland": "IE",
    "spain": "ES",
    "italy": "IT",
    "south korea": "KR",
    "korea": "KR",
}

LANGUAGE_ALIASES: dict[str, str] = {
    "english": "en",
    "en-us": "en",
    "en-gb": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "portuguese": "pt",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "hindi": "hi",
    "arabic": "ar",
}

DOMAIN_PREFIXES = ("http://", "https://", "www.")
DOMAIN_SUFFIXES = ("/",)


class SignalNormalizer:
    """Pure deterministic normalization — no randomness."""

    def normalize(self, event: EvidenceEvent) -> EvidenceEvent:
        return event.model_copy(
            update={
                "company_name": self.company(event.company_name) if event.company_name else None,
                "country": self.country(event.country),
                "language": self.language(event.language),
                "published_at": self._utc(event.published_at),
                "captured_at": self._utc(event.captured_at),
                "headline": self._clean_text(event.headline),
                "summary": self._clean_text(event.summary),
                "url": self.url(event.url) if event.url else None,
            }
        )

    def company(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value.strip())
        cleaned = re.sub(r"\b(Inc|LLC|Ltd|Corp|Co|GmbH|AG|SAS|Pty|Ltd)\.?\s*$", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip() or value.strip()

    def country(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized = value.strip().lower()
        alias = COUNTRY_ALIASES.get(normalized)
        if alias:
            return alias
        stripped = value.strip()
        if len(stripped) == 2:
            return stripped.upper()
        return stripped

    def language(self, value: str | None) -> str:
        if not value:
            return "unknown"
        normalized = value.strip().lower()
        return LANGUAGE_ALIASES.get(normalized, normalized)

    def url(self, value: str | None) -> str | None:
        if not value:
            return None
        cleaned = value.strip()
        for prefix in DOMAIN_PREFIXES:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        for suffix in DOMAIN_SUFFIXES:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
        return cleaned or value.strip()

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
