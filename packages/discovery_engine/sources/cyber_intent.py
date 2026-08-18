"""Intent-first cybersecurity buying-event source for DiscoveryEngine."""

from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from packages.cybersecurity_discovery.classifier import match_buying_events
from packages.cybersecurity_discovery.rejects import first_reject_reason
from packages.cybersecurity_discovery.sources import discover_sources
from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany


class CyberIntentDiscovery(DiscoverySource):
    """Discover public cybersecurity buying events. Never scans targets."""

    @property
    def name(self) -> str:
        return "cyber_intent"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        raw = await discover_sources(limit=limit)
        companies: list[DiscoveredCompany] = []
        for item in raw:
            if first_reject_reason(item.text):
                continue
            hits = match_buying_events(item.text)
            if not hits:
                continue
            host = ""
            if item.company_url_hint:
                host = urlparse(item.company_url_hint).netloc.lower().removeprefix("www.")
            companies.append(
                DiscoveredCompany(
                    company_name=item.company_hint or item.author or "Unknown",
                    domain=host,
                    source=self.name,
                    discovery_reason=hits[0][1][:180],
                    discovery_date=date.today(),
                    founder_name=item.author or "",
                    founder_role="Poster",
                    founder_source=item.source_url,
                    founder_confidence=0.5,
                    buying_signals=[h[1] for h in hits],
                    buying_signal_sources=[item.source_url],
                    country=item.country_hint or "",
                    metadata={
                        "source_url": item.source_url,
                        "source_name": item.source_name,
                        "title": item.title,
                    },
                )
            )
        return companies[:limit]
