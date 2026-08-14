"""Discover opportunities through startup communities and founder forums."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class StartupCommunityDiscovery(DiscoverySource):
    """Search startup communities for active technical requirements."""

    @property
    def name(self) -> str:
        return "startup_community"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        opportunities: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            '"looking for developer" site:indiehackers.com',
            '"need technical cofounder" site:indiehackers.com',
            '"building MVP" site:indiehackers.com',
            '"looking for agency" site:indiehackers.com',
            '"need SaaS developer" site:indiehackers.com',
            '"looking for developer" site:news.ycombinator.com',
            '"need technical team" site:news.ycombinator.com',
            '"looking for CTO" site:news.ycombinator.com',
            '"RFP" "development" site:news.ycombinator.com',
            '"looking for developer" site:reddit.com/r/startups',
            '"need development team" site:reddit.com/r/SaaS',
            '"looking for agency" site:reddit.com/r/Entrepreneur',
            '"need MVP developer" site:reddit.com/r/microsaas',
            '"looking for technical partner" site:reddit.com/r/startups',
            '"need help building" site:reddit.com/r/SaaS',
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

                # Extract platform
                platform = self._extract_platform(url)

                # Extract author
                author = self._extract_author(url, title, excerpt_text)

                # Extract company/project
                company_name = self._extract_company(title, excerpt_text)

                # Extract requirement
                requirement = self._extract_requirement(title, excerpt_text)

                # Skip if no meaningful requirement
                if not requirement:
                    continue

                # Create unique key
                dedup_key = f"{author}_{company_name}_{requirement[:50]}".lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Extract post date
                post_date = self._extract_date(excerpt_text)

                opportunity = DiscoveredCompany(
                    company_name=company_name or "Unknown",
                    domain="",
                    source="startup_community",
                    discovery_reason=f"Community post: {requirement[:100]}",
                    discovery_date=date.today(),
                    business_stage="early",
                    founder_name=author,
                    founder_role="Poster",
                    founder_source=url,
                    founder_confidence=0.7,
                    buying_signals=[requirement],
                    buying_signal_sources=[url],
                    metadata={
                        "source_url": url,
                        "source_platform": platform,
                        "post_author": author,
                        "post_title": title,
                        "exact_requirement": requirement,
                        "intent_level": "ACTIVE_REQUIREMENT",
                        "post_date": post_date,
                    },
                )
                opportunities.append(opportunity)
                logger.info("  DISCOVERED: %s — %s", author, requirement[:80])

        return opportunities[:limit]

    def _extract_platform(self, url: str) -> str:
        """Extract platform from URL."""
        if "indiehackers.com" in url.lower():
            return "indiehackers"
        elif "news.ycombinator.com" in url.lower():
            return "hackernews"
        elif "reddit.com" in url.lower():
            return "reddit"
        elif "producthunt.com" in url.lower():
            return "producthunt"
        else:
            return "unknown"

    def _extract_author(self, url: str, title: str, excerpt: str) -> str:
        """Extract author from post."""
        combined = f"{title}. {excerpt}"

        # Try to extract from URL
        if "reddit.com" in url.lower():
            user_match = re.search(r'/(?:user|u)/([A-Za-z0-9_-]+)', url)
            if user_match:
                return user_match.group(1)

        if "indiehackers.com" in url.lower():
            user_match = re.search(r'indiehackers\.com/([A-Za-z0-9_-]+)', url)
            if user_match:
                return user_match.group(1)

        # Try to extract from excerpt
        author_patterns = [
            r'(?:by|from|posted by|author)\s+([A-Za-z0-9_-]+)',
            r'([A-Za-z0-9_-]+)\s+(?:says|said|posted)',
        ]

        for pattern in author_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                author = match.group(1).strip()
                if len(author) >= 3:
                    return author

        return "Unknown"

    def _extract_company(self, title: str, excerpt: str) -> str:
        """Extract company/project name if mentioned."""
        combined = f"{title}. {excerpt}"

        # Look for company patterns
        company_patterns = [
            r'(?:my startup|our startup|our company|our project|my project)\s+([A-Z][A-Za-z\s]+)',
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:is|are)\s+(?:looking|seeking|hiring)',
            r'(?:for|at|to)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, combined)
            if match:
                company = match.group(1).strip()
                if len(company) >= 3 and len(company) <= 50:
                    return company

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

    def _extract_date(self, text: str) -> str:
        """Extract post date."""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\w+ \d{1,2}, \d{4})',
            r'(\d+ days? ago)',
            r'(\d+ hours? ago)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""
