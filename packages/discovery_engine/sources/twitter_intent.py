"""Discover opportunities through X/Twitter posts expressing need for technical services."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class TwitterIntentDiscovery(DiscoverySource):
    """Find public posts on X/Twitter expressing need for developers or agencies."""

    @property
    def name(self) -> str:
        return "twitter_intent"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        opportunities: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            '"looking for a developer" site:twitter.com OR site:x.com',
            '"looking for developers" site:twitter.com OR site:x.com',
            '"need a development team" site:twitter.com OR site:x.com',
            '"looking for CTO" site:twitter.com OR site:x.com',
            '"looking for technical cofounder" site:twitter.com OR site:x.com',
            '"need someone to build" site:twitter.com OR site:x.com',
            '"looking for agency" site:twitter.com OR site:x.com',
            '"need an MVP" site:twitter.com OR site:x.com',
            '"building a SaaS" site:twitter.com OR site:x.com',
            '"looking for React developer" site:twitter.com OR site:x.com',
            '"looking for Flutter developer" site:twitter.com OR site:x.com',
            '"looking for AI developer" site:twitter.com OR site:x.com',
            '"need an AI solution" site:twitter.com OR site:x.com',
            '"looking for technical partner" site:twitter.com OR site:x.com',
            '"need help building" site:twitter.com OR site:x.com',
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

                # Only process Twitter/X URLs
                if "twitter.com" not in url.lower() and "x.com" not in url.lower():
                    continue

                # Extract author handle
                author_handle = self._extract_author_handle(url, title, excerpt_text)

                # Extract author name
                author_name = self._extract_author_name(title, excerpt_text)

                # Extract requirement
                requirement = self._extract_requirement(title, excerpt_text)

                # Skip if no meaningful requirement
                if not requirement:
                    continue

                # Extract company/project if mentioned
                company_name = self._extract_company(title, excerpt_text)

                # Create unique key
                dedup_key = f"{author_handle}_{requirement[:50]}".lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Extract post date
                post_date = self._extract_date(excerpt_text)

                opportunity = DiscoveredCompany(
                    company_name=company_name or "Unknown",
                    domain="",
                    source="twitter_intent",
                    discovery_reason=f"Twitter post: {requirement[:100]}",
                    discovery_date=date.today(),
                    business_stage="early",
                    founder_name=author_name or author_handle,
                    founder_role="Poster",
                    founder_source=url,
                    founder_confidence=0.7,
                    buying_signals=[requirement],
                    buying_signal_sources=[url],
                    metadata={
                        "source_url": url,
                        "source_platform": "twitter",
                        "author_handle": author_handle,
                        "author_name": author_name,
                        "post_title": title,
                        "exact_requirement": requirement,
                        "intent_level": "ACTIVE_REQUIREMENT",
                        "post_date": post_date,
                    },
                )
                opportunities.append(opportunity)
                logger.info("  DISCOVERED: %s — %s", author_handle, requirement[:80])

        return opportunities[:limit]

    def _extract_author_handle(self, url: str, title: str, excerpt: str) -> str:
        """Extract Twitter handle from URL."""
        # Try to extract from URL
        handle_match = re.search(r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)', url)
        if handle_match:
            return handle_match.group(1)

        # Try to extract from excerpt
        handle_match = re.search(r'@([A-Za-z0-9_]+)', f"{title} {excerpt}")
        if handle_match:
            return handle_match.group(1)

        return "Unknown"

    def _extract_author_name(self, title: str, excerpt: str) -> str:
        """Extract author name from post."""
        combined = f"{title}. {excerpt}"

        # Look for name patterns
        name_patterns = [
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(?:@|says|said|posted)',
            r'(?:by|from|posted by)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, combined)
            if match:
                name = match.group(1).strip()
                if len(name) >= 3:
                    return name

        return ""

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

    def _extract_company(self, title: str, excerpt: str) -> str:
        """Extract company/project name if mentioned."""
        combined = f"{title}. {excerpt}"

        # Look for company patterns
        company_patterns = [
            r'(?:my startup|our startup|our company|our project|my project)\s+([A-Z][A-Za-z\s]+)',
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:is|are)\s+(?:looking|seeking|hiring)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, combined)
            if match:
                company = match.group(1).strip()
                if len(company) >= 3 and len(company) <= 50:
                    return company

        return ""

    def _extract_date(self, text: str) -> str:
        """Extract post date if available."""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\w+ \d{1,2}, \d{4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""
