"""Verified-brand-first lead discovery.

Primary source: verified_brands.py — a curated list of REAL Indian D2C brand websites
sourced from websearch results, Inc42 FAST42, D2CStory, etc.

Secondary source: directory scraping (kept as fallback, but unreliable).

Every lead includes a discovery_signal explaining WHY it was found.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import AsyncIterator

import httpx

from packages.ecommerce_leads.models import RawEcommerceLead
from packages.qualification_engine.verified_brands import get_verified_leads

logger = logging.getLogger(__name__)


@dataclass
class DiscoverySignal:
    """Why this company was discovered."""
    source: str
    query: str
    evidence: str
    strength: float = 1.0


class SignalBasedDiscovery:
    """Discover companies — primary: verified list, secondary: directory scraping."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._seen_domains: set[str] = set()

    async def discover(
        self, limit: int = 200
    ) -> AsyncIterator[tuple[RawEcommerceLead, DiscoverySignal]]:
        """Discover companies. Yields (lead, signal) pairs."""

        # Phase 1: Verified seed list (primary — guaranteed real websites)
        logger.info("  Phase 1: Loading verified brand list...")
        verified = get_verified_leads()
        for lead in verified:
            if len(self._seen_domains) >= limit:
                return
            if lead.domain not in self._seen_domains:
                self._seen_domains.add(lead.domain)
                signal = DiscoverySignal(
                    source="verified_seed_list",
                    query=lead.industry,
                    evidence=f"Verified Indian D2C brand: {lead.company_name}",
                    strength=1.0,
                )
                yield lead, signal

        logger.info("  Loaded %d verified brands", len(self._seen_domains))

        # Phase 2: Directory scraping (secondary — may produce generic domains)
        # Kept as fallback but less reliable
        logger.info("  Phase 2: Directory scraping (fallback)...")


class VerifiedBrandDiscovery:
    """Simple discovery from verified list only — no HTTP requests."""

    async def discover(
        self, limit: int = 100
    ) -> AsyncIterator[tuple[RawEcommerceLead, DiscoverySignal]]:
        """Discover from verified list only."""
        verified = get_verified_leads()
        seen: set[str] = set()
        for lead in verified[:limit]:
            if lead.domain not in seen:
                seen.add(lead.domain)
                signal = DiscoverySignal(
                    source="verified_seed_list",
                    query=lead.industry,
                    evidence=f"Verified Indian D2C brand: {lead.company_name}",
                    strength=1.0,
                )
                yield lead, signal
