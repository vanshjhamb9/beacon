"""Discover opportunities through Reddit posts expressing need for technical services."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class RedditIntentDiscovery(DiscoverySource):
    """Find posts on Reddit expressing need for developers, agencies, or technical teams."""

    @property
    def name(self) -> str:
        return "reddit_intent"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        opportunities: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            '"looking for developer" site:reddit.com',
            '"looking for development team" site:reddit.com',
            '"need technical cofounder" site:reddit.com',
            '"need CTO" site:reddit.com',
            '"need MVP developer" site:reddit.com',
            '"build my startup" site:reddit.com',
            '"looking for software agency" site:reddit.com',
            '"looking for app developer" site:reddit.com',
            '"need SaaS developer" site:reddit.com',
            '"need AI developer" site:reddit.com',
            '"need automation" site:reddit.com',
            '"technical team needed" site:reddit.com',
            '"development partner" site:reddit.com',
            '"need help building" site:reddit.com',
            '"looking for React developer" site:reddit.com',
            '"looking for Flutter developer" site:reddit.com',
            '"need backend developer" site:reddit.com',
            '"looking for agency" site:reddit.com',
            '"need someone to build" site:reddit.com',
            '"RFP development" site:reddit.com',
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

                # Only process Reddit URLs
                if "reddit.com" not in url.lower():
                    continue

                # Extract person/author from URL
                author = self._extract_author(url, title, excerpt_text)

                # Extract requirement from title and excerpts
                requirement = self._extract_requirement(title, excerpt_text)

                # Skip if no meaningful requirement found
                if not requirement:
                    continue

                # Extract company/project if mentioned
                company_name = self._extract_company(title, excerpt_text)

                # Create unique key to deduplicate
                dedup_key = f"{author}_{company_name}_{requirement[:50]}".lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Extract subreddit
                subreddit = self._extract_subreddit(url)

                # Extract location if mentioned
                location = self._extract_location(excerpt_text)

                # Determine intent level
                intent_level = self._classify_intent(requirement, excerpt_text)

                opportunity = DiscoveredCompany(
                    company_name=company_name or "Unknown",
                    domain="",
                    source="reddit_intent",
                    discovery_reason=f"Reddit post: {requirement[:100]}",
                    discovery_date=date.today(),
                    business_stage="early",
                    founder_name=author,
                    founder_role="Poster",
                    founder_source=url,
                    founder_confidence=0.7,
                    buying_signals=[requirement],
                    buying_signal_sources=[url],
                    growth_signals=[],
                    metadata={
                        "source_url": url,
                        "source_platform": "reddit",
                        "subreddit": subreddit,
                        "post_title": title,
                        "post_author": author,
                        "exact_requirement": requirement,
                        "intent_level": intent_level,
                        "location": location,
                    },
                )
                opportunities.append(opportunity)
                logger.info("  DISCOVERED: %s — %s", author, requirement[:80])

        return opportunities[:limit]

    def _extract_author(self, url: str, title: str, excerpt: str) -> str:
        """Extract author/username from Reddit post."""
        # Try to extract from URL pattern: /user/username/ or /u/username/
        user_match = re.search(r'/(?:user|u)/([A-Za-z0-9_-]+)', url)
        if user_match:
            return user_match.group(1)

        # Try to extract from title pattern: "by username" or "posted by username"
        by_match = re.search(r'(?:by|posted by|from)\s+([A-Za-z0-9_-]+)', title + " " + excerpt)
        if by_match:
            return by_match.group(1)

        return "Unknown"

    def _extract_requirement(self, title: str, excerpt: str) -> str:
        """Extract the exact requirement from the post."""
        combined = f"{title}. {excerpt}"

        # Look for explicit requirement patterns
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
                # Clean up
                requirement = re.sub(r'\s+', ' ', requirement)
                if len(requirement) > 10:
                    return requirement

        # Fallback: use title if it contains intent signals
        intent_signals = ["looking for", "need", "hire", "developer", "team", "agency", "build"]
        if any(signal in title.lower() for signal in intent_signals):
            return title.strip()

        return ""

    def _extract_company(self, title: str, excerpt: str) -> str:
        """Extract company/project name if mentioned."""
        combined = f"{title}. {excerpt}"

        # Look for company name patterns
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

    def _extract_subreddit(self, url: str) -> str:
        """Extract subreddit from URL."""
        match = re.search(r'/r/([A-Za-z0-9_]+)', url)
        return match.group(1) if match else "unknown"

    def _extract_location(self, text: str) -> str:
        """Extract location if mentioned."""
        location_patterns = [
            r'(?:in|from|based in|located in)\s+([A-Z][A-Za-z\s]+?)(?:\.|,|\s+(?:and|or|with|looking|need))',
            r'(?:India|USA|UK|Canada|Australia|Germany|Singapore)',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()

        return ""

    def _classify_intent(self, requirement: str, excerpt: str) -> str:
        """Classify intent level based on requirement."""
        combined = f"{requirement}. {excerpt}".lower()

        # ACTIVE_REQUIREMENT (90-100)
        active_signals = [
            "looking for developer",
            "need developer",
            "need development team",
            "looking for agency",
            "need MVP",
            "need someone to build",
            "need help building",
            "hiring developer",
            "hire developer",
            "need technical cofounder",
            "need CTO",
        ]
        if any(signal in combined for signal in active_signals):
            return "ACTIVE_REQUIREMENT"

        # EVALUATION (70-89)
        evaluation_signals = [
            "comparing",
            "evaluating",
            "pricing",
            "how much",
            "cost",
            "budget",
            "proposal",
        ]
        if any(signal in combined for signal in evaluation_signals):
            return "EVALUATION"

        # EARLY_INTENT (50-69)
        early_signals = [
            "planning to",
            "going to",
            "thinking about",
            "want to build",
            "idea for",
        ]
        if any(signal in combined for signal in early_signals):
            return "EARLY_INTENT"

        return "COMPANY_OPPORTUNITY"
