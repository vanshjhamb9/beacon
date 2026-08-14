"""Discover companies through job hiring signals."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class HiringDiscovery(DiscoverySource):
    """Find companies that are actively hiring (growth signal)."""

    @property
    def name(self) -> str:
        return "hiring_signals"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        companies: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            "Indian D2C brand hiring ecommerce manager 2026",
            "India startup hiring growth marketer D2C 2026",
            "Indian D2C company hiring head of operations 2026",
            "India ecommerce brand hiring supply chain manager 2026",
            "Indian D2C startup hiring social media manager 2026",
            "India new age brand hiring brand manager 2026",
        ]

        for query in queries:
            if len(companies) >= limit:
                break

            try:
                results = await websearch(query=query, numResults=10)
            except Exception as e:
                logger.warning("Websearch failed for '%s': %s", query, e)
                continue

            if not results or not results.get("results"):
                continue

            for result in results["results"]:
                if len(companies) >= limit:
                    break

                title = result.get("title", "")
                url = result.get("url", "")
                excerpts = result.get("excerpts", [])
                excerpt_text = " ".join(excerpts) if excerpts else ""

                # Look for company names in hiring context
                hiring_patterns = [
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:is hiring|are hiring|hiring|looking for|seeking|wants|joins|joins as)',
                    r'(?:at|for|at)\s+([A-Z][A-Za-z\s&\'\.]+?)\s+(?:is|are|has|have)',
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:careers?|jobs?|openings?)',
                ]

                company_matches = []
                for pattern in hiring_patterns:
                    matches = re.findall(pattern, excerpt_text + " " + title)
                    company_matches.extend(matches)

                for match in company_matches:
                    company_name = match.strip()
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = company_name.strip(".,;:!?\"'")

                    if len(company_name) < 3 or len(company_name) > 50:
                        continue
                    if company_name.lower() in seen:
                        continue

                    skip_words = [
                        "the", "this", "that", "from", "with", "into", "through",
                        "india", "indian", "d2c", "startup", "brand", "company",
                        "linkedin", "naukri", "indeed", "glassdoor",
                    ]
                    if company_name.lower().split()[0] in skip_words:
                        continue

                    seen.add(company_name.lower())

                    # Extract role being hired for
                    role_match = re.search(
                        r'(?:hiring|looking for|seeking)\s+(?:a\s+)?([A-Za-z\s]+?)(?:\s+(?:at|for|in|to|with|\.|,|$))',
                        excerpt_text,
                    )
                    role = role_match.group(1).strip() if role_match else "team member"

                    domain_guess = self._guess_domain(company_name)

                    company = DiscoveredCompany(
                        company_name=company_name,
                        domain=domain_guess,
                        source="hiring_signals",
                        discovery_reason=f"Actively hiring for {role}",
                        discovery_date=date.today(),
                        business_stage="growing",
                        growth_signals=[f"Hiring: {role}"],
                        growth_signal_sources=[url],
                        metadata={
                            "hired_role": role,
                            "article_url": url,
                            "query": query,
                        },
                    )
                    companies.append(company)
                    logger.info("  DISCOVERED: %s — Hiring: %s", company_name, role)

        return companies[:limit]

    def _guess_domain(self, company_name: str) -> str:
        base = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        base = re.sub(r'\s+', '', base)
        return f"{base}.com"
