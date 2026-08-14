"""Discover opportunities through Upwork project requirements."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class UpworkIntentDiscovery(DiscoverySource):
    """Find public project requirements on Upwork relevant to Inowix."""

    @property
    def name(self) -> str:
        return "upwork_intent"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        opportunities: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            '"SaaS development" site:upwork.com',
            '"AI development" site:upwork.com',
            '"mobile app development" site:upwork.com',
            '"web application" site:upwork.com',
            '"MVP development" site:upwork.com',
            '"custom software" site:upwork.com',
            '"automation" site:upwork.com',
            '"API integration" site:upwork.com',
            '"ecommerce development" site:upwork.com',
            '"chatbot development" site:upwork.com',
            '"React developer" site:upwork.com',
            '"Flutter developer" site:upwork.com',
            '"Node.js developer" site:upwork.com',
            '"Python developer" site:upwork.com',
            '"full stack developer" site:upwork.com',
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

                # Only process Upwork URLs
                if "upwork.com" not in url.lower():
                    continue

                # Extract project title
                project_title = self._extract_project_title(url, title, excerpt_text)

                # Extract requirement
                requirement = self._extract_requirement(title, excerpt_text)

                # Skip if no meaningful requirement
                if not requirement:
                    continue

                # Extract client/company if available
                client_name = self._extract_client(title, excerpt_text)

                # Extract budget if available
                budget = self._extract_budget(excerpt_text)

                # Extract skills required
                skills = self._extract_skills(excerpt_text)

                # Create unique key
                dedup_key = f"{project_title}_{requirement[:50]}".lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Extract posting date
                post_date = self._extract_date(excerpt_text)

                opportunity = DiscoveredCompany(
                    company_name=client_name or "Unknown",
                    domain="",
                    source="upwork_intent",
                    discovery_reason=f"Upwork project: {requirement[:100]}",
                    discovery_date=date.today(),
                    business_stage="early",
                    founder_name=client_name,
                    founder_role="Client",
                    founder_source=url,
                    founder_confidence=0.6,
                    buying_signals=[requirement],
                    buying_signal_sources=[url],
                    technology_signals=skills,
                    metadata={
                        "source_url": url,
                        "source_platform": "upwork",
                        "project_title": project_title,
                        "client_name": client_name,
                        "budget": budget,
                        "skills_required": skills,
                        "exact_requirement": requirement,
                        "intent_level": "ACTIVE_REQUIREMENT",
                        "post_date": post_date,
                    },
                )
                opportunities.append(opportunity)
                logger.info("  DISCOVERED: %s — %s", project_title, requirement[:80])

        return opportunities[:limit]

    def _extract_project_title(self, url: str, title: str, excerpt: str) -> str:
        """Extract project title from Upwork."""
        # Try to extract from URL
        url_match = re.search(r'upwork\.com/jobs/([A-Za-z0-9_-]+)', url)
        if url_match:
            return url_match.group(1).replace("-", " ").title()

        # Try to extract from title
        title_match = re.search(r'[-–—]\s*(.+?)(?:\s+[-–—]|$)', title)
        if title_match:
            return title_match.group(1).strip()

        return "Unknown"

    def _extract_requirement(self, title: str, excerpt: str) -> str:
        """Extract requirement from Upwork post."""
        combined = f"{title}. {excerpt}"

        # Look for requirement patterns
        requirement_patterns = [
            r'(?:looking for|need|seeking|searching for)\s+(.{10,100}?)(?:\.|$)',
            r'(?:anyone know|recommend)\s+(?:a\s+)?(.{10,100}?)(?:\.|$)',
            r'(?:hiring|hire)\s+(?:a\s+)?(.{10,100}?)(?:\.|$)',
            r'(?:want to|trying to|want someone to)\s+(.{10,100}?)(?:\.|$)',
            r'(?:project requires|need someone to)\s+(.{10,100}?)(?:\.|$)',
        ]

        for pattern in requirement_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                requirement = match.group(1).strip()
                requirement = re.sub(r'\s+', ' ', requirement)
                if len(requirement) > 10:
                    return requirement

        # Fallback: use title if it contains relevant keywords
        relevant_keywords = ["development", "developer", "app", "website", "saas", "ai", "automation", "api"]
        if any(keyword in title.lower() for keyword in relevant_keywords):
            return title.strip()

        return ""

    def _extract_client(self, title: str, excerpt: str) -> str:
        """Extract client name if available."""
        combined = f"{title}. {excerpt}"

        # Look for client patterns
        client_patterns = [
            r'(?:client|company|business)\s+([A-Z][A-Za-z\s]+)',
            r'(?:posted by|from)\s+([A-Z][A-Za-z\s]+)',
        ]

        for pattern in client_patterns:
            match = re.search(pattern, combined)
            if match:
                client = match.group(1).strip()
                if len(client) >= 3 and len(client) <= 50:
                    return client

        return ""

    def _extract_budget(self, text: str) -> str:
        """Extract budget if available."""
        budget_patterns = [
            r'\$[\d,.]+(?:\s*-\s*\$[\d,.]+)?',
            r'(?:budget|price|cost)[:\s]+(\$[\d,.]+)',
            r'([\d,.]+)\s*(?:USD|INR|EUR)',
        ]

        for pattern in budget_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return ""

    def _extract_skills(self, text: str) -> list[str]:
        """Extract required skills."""
        skill_patterns = [
            r'(?:skills?|requirements?|technologies?)[:\s]+(.+?)(?:\.|$)',
            r'(?:React|Node\.js|Python|Flutter|Swift|Kotlin|Java|TypeScript|AWS|Docker|Kubernetes)',
        ]

        skills = []
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    skills.extend([s.strip() for s in match.split(",") if s.strip()])

        return list(set(skills))[:10]  # Limit to 10 skills

    def _extract_date(self, text: str) -> str:
        """Extract posting date."""
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
