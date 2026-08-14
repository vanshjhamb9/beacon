"""Discover companies through new store/brand launch signals."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class NewLaunchDiscovery(DiscoverySource):
    """Find companies that recently launched new stores or products."""

    @property
    def name(self) -> str:
        return "new_launches"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        companies: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            "new Indian D2C brand launched 2026",
            "India Shopify store launched 2025 2026",
            "Indian D2C brand new product launch 2026",
            "India new ecommerce brand direct to consumer 2026",
            "Indian D2C startup new collection launch 2026",
            "India new beauty fashion brand launch 2026",
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

                # Look for launch/new brand mentions
                launch_patterns = [
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:launches?|launched|unveils?|unveiled|introduces?|introduced|debuts?|debuted)',
                    r'(?:new|launching|launched)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:brand|store|collection|product|platform|app|website))',
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:brand|store|collection)\s+(?:is now|has been|just)',
                ]

                company_matches = []
                for pattern in launch_patterns:
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

                    # Detect what was launched
                    launch_type = "new brand/store"
                    if re.search(r'(?:product|collection|line|range)', excerpt_text, re.I):
                        launch_type = "new product/collection"
                    elif re.search(r'(?:store|outlet|retail|offline)', excerpt_text, re.I):
                        launch_type = "new store/outlet"
                    elif re.search(r'(?:app|platform|website)', excerpt_text, re.I):
                        launch_type = "new app/platform"

                    domain_guess = self._guess_domain(company_name)

                    company = DiscoveredCompany(
                        company_name=company_name,
                        domain=domain_guess,
                        source="new_launches",
                        discovery_reason=f"Recently launched {launch_type}",
                        discovery_date=date.today(),
                        business_stage="early",
                        growth_signals=[f"New launch: {launch_type}"],
                        growth_signal_sources=[url],
                        metadata={
                            "launch_type": launch_type,
                            "article_url": url,
                            "query": query,
                        },
                    )
                    companies.append(company)
                    logger.info("  DISCOVERED: %s — %s", company_name, launch_type)

        return companies[:limit]

    def _guess_domain(self, company_name: str) -> str:
        base = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        base = re.sub(r'\s+', '', base)
        return f"{base}.com"
