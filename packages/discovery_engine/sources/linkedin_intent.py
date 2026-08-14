"""Discover opportunities through LinkedIn posts expressing need for technical services."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class LinkedInIntentDiscovery(DiscoverySource):
    """Find founders on LinkedIn requesting developers or announcing product builds."""

    @property
    def name(self) -> str:
        return "linkedin_intent"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        opportunities: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            '"looking for developer" site:linkedin.com',
            '"looking for development team" site:linkedin.com',
            '"need technical cofounder" site:linkedin.com',
            '"building MVP" site:linkedin.com',
            '"looking for agency" site:linkedin.com',
            '"need SaaS developer" site:linkedin.com',
            '"looking for technical partner" site:linkedin.com',
            '"startup" "need developers" site:linkedin.com',
            '"founder" "looking for CTO" site:linkedin.com',
            '"need help building" site:linkedin.com',
            '"looking for React developer" site:linkedin.com',
            '"looking for Flutter developer" site:linkedin.com',
            '"need backend developer" site:linkedin.com',
            '"looking for AI developer" site:linkedin.com',
            '"need automation" site:linkedin.com',
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

                # Only process LinkedIn URLs
                if "linkedin.com" not in url.lower():
                    continue

                # Extract person name
                person_name = self._extract_person(url, title, excerpt_text)

                # Extract company name
                company_name = self._extract_company(url, title, excerpt_text)

                # Extract requirement
                requirement = self._extract_requirement(title, excerpt_text)

                # Skip if no meaningful requirement
                if not requirement:
                    continue

                # Create unique key
                dedup_key = f"{person_name}_{company_name}_{requirement[:50]}".lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Extract person role
                person_role = self._extract_role(excerpt_text)

                # Extract LinkedIn profile URL
                linkedin_url = self._extract_linkedin_profile(url, excerpt_text)

                opportunity = DiscoveredCompany(
                    company_name=company_name or "Unknown",
                    domain="",
                    source="linkedin_intent",
                    discovery_reason=f"LinkedIn post: {requirement[:100]}",
                    discovery_date=date.today(),
                    business_stage="early",
                    founder_name=person_name,
                    founder_role=person_role,
                    founder_source=linkedin_url or url,
                    founder_confidence=0.8,
                    buying_signals=[requirement],
                    buying_signal_sources=[url],
                    metadata={
                        "source_url": url,
                        "source_platform": "linkedin",
                        "person_name": person_name,
                        "person_role": person_role,
                        "company_name": company_name,
                        "linkedin_profile": linkedin_url,
                        "exact_requirement": requirement,
                        "intent_level": "ACTIVE_REQUIREMENT",
                    },
                )
                opportunities.append(opportunity)
                logger.info("  DISCOVERED: %s — %s", person_name, requirement[:80])

        return opportunities[:limit]

    def _extract_person(self, url: str, title: str, excerpt: str) -> str:
        """Extract person name from LinkedIn."""
        combined = f"{title}. {excerpt}"

        # Look for name patterns
        name_patterns = [
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(?:on LinkedIn|posted|says)',
            r'(?:by|from|posted by)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(?:Co-Founder|Founder|CEO|CTO|VP)',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, combined)
            if match:
                name = match.group(1).strip()
                if len(name) >= 3:
                    return name

        # Try to extract from URL
        url_match = re.search(r'linkedin\.com/in/([A-Za-z0-9_-]+)', url)
        if url_match:
            return url_match.group(1).replace("-", " ").title()

        return "Unknown"

    def _extract_company(self, url: str, title: str, excerpt: str) -> str:
        """Extract company name from LinkedIn."""
        combined = f"{title}. {excerpt}"

        # Look for company patterns
        company_patterns = [
            r'(?:Co-Founder|Founder|CEO|CTO|VP)\s+at\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:on|,|\.|$))',
            r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:is|are)\s+(?:looking|seeking|hiring)',
            r'(?:my startup|our startup|our company|our project)\s+([A-Z][A-Za-z\s]+)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, combined)
            if match:
                company = match.group(1).strip()
                if len(company) >= 3 and len(company) <= 50:
                    return company

        return ""

    def _extract_requirement(self, title: str, excerpt: str) -> str:
        """Extract requirement from LinkedIn post."""
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

    def _extract_role(self, text: str) -> str:
        """Extract person role from text."""
        role_patterns = [
            r'(Co-Founder|Founder|CEO|CTO|VP|Head of|Director)',
        ]

        for pattern in role_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return "Founder"

    def _extract_linkedin_profile(self, url: str, excerpt: str) -> str:
        """Extract LinkedIn profile URL."""
        # Try to extract from URL
        profile_match = re.search(r'linkedin\.com/in/([A-Za-z0-9_-]+)', url)
        if profile_match:
            return f"https://www.linkedin.com/in/{profile_match.group(1)}"

        # Try to extract from excerpt
        profile_match = re.search(r'linkedin\.com/in/([A-Za-z0-9_-]+)', excerpt)
        if profile_match:
            return f"https://www.linkedin.com/in/{profile_match.group(1)}"

        return ""
