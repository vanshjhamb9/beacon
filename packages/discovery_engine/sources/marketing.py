"""Discover companies through marketing and advertising signals."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class MarketingDiscovery(DiscoverySource):
    """Find companies with active marketing/advertising."""

    @property
    def name(self) -> str:
        return "marketing_activity"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        companies: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            "Indian D2C brand Instagram marketing strategy 2026",
            "India ecommerce brand Meta ads advertising 2026",
            "Indian D2C brand social media growth 2026",
            "India new brand digital marketing campaign 2026",
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

                # Look for company names in marketing context
                marketing_patterns = [
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:campaign|ads|marketing|social media|Instagram|growth|engagement)',
                    r'(?:brand|company|startup)\s+([A-Z][A-Za-z\s&\'\.]+?)\s+(?:marketing|ads|social|digital)',
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:D2C|DTC|brand)\s+(?:marketing|ads|strategy)',
                ]

                company_matches = []
                for pattern in marketing_patterns:
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
                    ]
                    if company_name.lower().split()[0] in skip_words:
                        continue

                    seen.add(company_name.lower())

                    domain_guess = self._guess_domain(company_name)

                    company = DiscoveredCompany(
                        company_name=company_name,
                        domain=domain_guess,
                        source="marketing_activity",
                        discovery_reason="Active marketing/advertising activity detected",
                        discovery_date=date.today(),
                        business_stage="growing",
                        growth_signals=["Active marketing/advertising"],
                        growth_signal_sources=[url],
                        metadata={
                            "article_url": url,
                            "query": query,
                        },
                    )
                    companies.append(company)
                    logger.info("  DISCOVERED: %s — Active marketing", company_name)

        return companies[:limit]

    def _guess_domain(self, company_name: str) -> str:
        base = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        base = re.sub(r'\s+', '', base)
        return f"{base}.com"
