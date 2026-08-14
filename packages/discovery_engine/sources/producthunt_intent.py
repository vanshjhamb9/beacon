"""Discover opportunities through Product Hunt posts expressing need for technical services."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class ProductHuntIntentDiscovery(DiscoverySource):
    """Find founders on Product Hunt who may need technical help."""

    @property
    def name(self) -> str:
        return "producthunt_intent"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        opportunities: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            '"Product Hunt" "looking for developer" site:producthunt.com',
            '"Product Hunt" "need technical cofounder" site:producthunt.com',
            '"Product Hunt" "building MVP" site:producthunt.com',
            '"Product Hunt" "looking for agency" site:producthunt.com',
            '"just launched" "need help building" site:producthunt.com',
            '"new product" "looking for development team" site:producthunt.com',
            '"Product Hunt launch" "need developer" site:producthunt.com',
            '"Product Hunt" "seeking technical" site:producthunt.com',
            '"Product Hunt" "need CTO" site:producthunt.com',
            '"Product Hunt" "looking for technical partner" site:producthunt.com',
        ]

        for query in queries:
            if len(opportunities) >= limit:
                break

            try:
                results = await websearch(query=query, numResults=10)
            except Exception as e:
                logger.warning("Websearch failed for '%s': %s", query, e)
                continue

            if not results or not results.get("results"):
                continue

            for result in results["results"]:
                if len(opportunities) >= limit:
                    break

                title = result.get("title", "")
                url = result.get("url", "")
                excerpts = result.get("excerpts", [])
                excerpt_text = " ".join(excerpts) if excerpts else ""

                # Only process Product Hunt URLs
                if "producthunt.com" not in url.lower():
                    continue

                # Extract founder name
                founder_name = self._extract_founder(url, title, excerpt_text)

                # Extract product name
                product_name = self._extract_product(url, title, excerpt_text)

                # Extract requirement
                requirement = self._extract_requirement(title, excerpt_text)

                # Skip if no meaningful requirement
                if not requirement:
                    continue

                # Create unique key
                dedup_key = f"{founder_name}_{product_name}_{requirement[:50]}".lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                opportunity = DiscoveredCompany(
                    company_name=product_name or "Unknown",
                    domain="",
                    source="producthunt_intent",
                    discovery_reason=f"Product Hunt post: {requirement[:100]}",
                    discovery_date=date.today(),
                    business_stage="early",
                    founder_name=founder_name,
                    founder_role="Founder",
                    founder_source=url,
                    founder_confidence=0.8,
                    buying_signals=[requirement],
                    buying_signal_sources=[url],
                    metadata={
                        "source_url": url,
                        "source_platform": "producthunt",
                        "product_name": product_name,
                        "founder_name": founder_name,
                        "exact_requirement": requirement,
                        "intent_level": "ACTIVE_REQUIREMENT",
                    },
                )
                opportunities.append(opportunity)
                logger.info("  DISCOVERED: %s — %s", founder_name, requirement[:80])

        return opportunities[:limit]

    def _extract_founder(self, url: str, title: str, excerpt: str) -> str:
        """Extract founder name from Product Hunt."""
        combined = f"{title}. {excerpt}"

        # Look for founder patterns
        founder_patterns = [
            r'(?:founder|created by|made by|built by|by)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(?:is the founder|founded|co-founder)',
        ]

        for pattern in founder_patterns:
            match = re.search(pattern, combined)
            if match:
                name = match.group(1).strip()
                if len(name) >= 3:
                    return name

        return "Unknown"

    def _extract_product(self, url: str, title: str, excerpt: str) -> str:
        """Extract product name from URL or title."""
        # Try to extract from URL
        url_match = re.search(r'producthunt\.com/posts/([A-Za-z0-9_-]+)', url)
        if url_match:
            return url_match.group(1).replace("-", " ").title()

        # Try to extract from title
        title_match = re.search(r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s[-–—]', title)
        if title_match:
            return title_match.group(1).strip()

        return "Unknown"

    def _extract_requirement(self, title: str, excerpt: str) -> str:
        """Extract requirement from post."""
        combined = f"{title}. {excerpt}"

        # Look for requirement patterns
        requirement_patterns = [
            r'(?:looking for|need|seeking|searching for)\s+(.{10,100}?)(?:\.|$)',
            r'(?:anyone know|recommend)\s+(?:a\s+)?(.{10,100}?)(?:\.|$)',
            r'(?:hiring|hire)\s+(?:a\s+)?(.{10,100}?)(?:\.|$)',
            r'(?:want to|trying to|want someone to)\s+(.{10,100}?)(?:\.|$)',
        ]

        for pattern in requirement_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                requirement = match.group(1).strip()
                requirement = re.sub(r'\s+', ' ', requirement)
                if len(requirement) > 10:
                    return requirement

        # Fallback: check for intent signals
        intent_signals = ["looking for", "need", "hire", "developer", "team", "agency", "build", "technical"]
        if any(signal in title.lower() for signal in intent_signals):
            return title.strip()

        return ""
