"""Apple App Store developer discovery via official iTunes Search API.

Phase 0: directory enrichment only — not an outbound lead source.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from collectors.events import NormalizedEvent
from collectors.freshness import parse_datetime
from intelligence.entity_resolution.platform_domains import is_platform_domain

ITUNES = "https://itunes.apple.com/search"

SKIP_PUBLISHERS = {
    "microsoft",
    "microsoft corporation",
    "google",
    "google llc",
    "apple",
    "apple inc",
    "amazon",
    "amazon.com",
    "meta",
    "meta platforms",
    "facebook",
    "samsung",
}


def _host(url: str | None) -> str | None:
    if not url:
        return None
    raw = url if "://" in url else f"https://{url}"
    try:
        host = urlparse(raw).netloc.lower().removeprefix("www.")
    except ValueError:
        return None
    if not host or is_platform_domain(host) or "apple.com" in host:
        return None
    return host


class AppStoreDeveloperCollector:
    source = "app_store"

    def __init__(
        self,
        *,
        max_items: int = 40,
        terms: list[str] | None = None,
        lead_eligible: bool = False,
    ) -> None:
        self.max_items = max_items
        self.terms = terms or ["saas", "ai productivity", "b2b", "crm", "automation"]
        self.lead_eligible = lead_eligible

    def collect(self) -> list[NormalizedEvent]:
        events: list[NormalizedEvent] = []
        seen: set[str] = set()
        now = datetime.now(UTC)
        with httpx.Client(timeout=15.0, headers={"User-Agent": "BeaconODU/1.0"}) as client:
            for term in self.terms:
                if len(events) >= self.max_items:
                    break
                try:
                    resp = client.get(
                        ITUNES,
                        params={"term": term, "entity": "software", "limit": 25, "country": "us"},
                    )
                    if resp.status_code >= 400:
                        continue
                    for item in resp.json().get("results") or []:
                        website = item.get("sellerUrl") or item.get("artistViewUrl")
                        host = _host(website)
                        if not host or host in seen:
                            continue
                        # Prefer sellerUrl as developer website
                        seller = _host(item.get("sellerUrl"))
                        if not seller:
                            continue
                        seen.add(seller)
                        name = str(item.get("sellerName") or item.get("artistName") or item.get("trackName") or "App")
                        if name.lower().strip() in SKIP_PUBLISHERS:
                            continue
                        track = str(item.get("trackName") or name)
                        release = parse_datetime(
                            item.get("currentVersionReleaseDate") or item.get("releaseDate")
                        ) or datetime(2008, 7, 10, tzinfo=UTC)
                        events.append(
                            NormalizedEvent(
                                source=self.source,
                                url=str(item.get("trackViewUrl") or f"https://{seller}"),
                                title=name,
                                content=str(item.get("description") or track)[:2000],
                                published_at=release,
                                metadata={
                                    "source_kind": "directory",
                                    "lead_eligible": self.lead_eligible,
                                    "enrichment_only": not self.lead_eligible,
                                    "official_website": f"https://{seller}",
                                    "homepage": f"https://{seller}",
                                    "official_domain": seller,
                                    "domain": seller,
                                    "developer_name": name,
                                    "publisher": item.get("sellerName") or item.get("artistName"),
                                    "support_url": item.get("sellerUrl"),
                                    "privacy_url": None,
                                    "company": name,
                                    "app_name": track,
                                    "company_hints": [name],
                                    "content_occurred_at": release.isoformat(),
                                    "currentVersionReleaseDate": item.get("currentVersionReleaseDate"),
                                    "directory_signals": [f"App Store listing: {track}"],
                                    "buying_signals": [],
                                    "website_attribution": {
                                        "website": f"https://{seller}",
                                        "source": "itunes_search_api",
                                        "confidence": 94.0,
                                        "collector": self.source,
                                        "verified_at": now.isoformat(),
                                    },
                                    "collector_version": "odu-app-store-v2-enrichment",
                                },
                            )
                        )
                        if len(events) >= self.max_items:
                            break
                except Exception:  # noqa: BLE001
                    continue
        return events
