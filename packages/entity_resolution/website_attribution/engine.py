"""Website attribution — where the official website came from."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from entity_resolution.models.types import OfficialWebsite, WebsiteAttribution, UNKNOWN


class WebsiteAttributionEngine:
    def attribute(self, website: OfficialWebsite, *, collector: str | None = None, payload: dict[str, Any] | None = None) -> WebsiteAttribution:
        payload = payload or {}
        return WebsiteAttribution(
            website=website.website,
            domain=website.domain,
            discovery_source=website.source if website.discovered else UNKNOWN,
            collector=str(collector or payload.get("source") or UNKNOWN),
            confidence=website.confidence if website.discovered else 0.0,
            timestamp=website.verified_at or datetime.now(UTC),
            evidence=list(website.evidence) + [f"collector:{collector or payload.get('source')}"],
        )
