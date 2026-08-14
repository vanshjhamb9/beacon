"""Discover companies through founder activity signals."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class FounderDiscovery(DiscoverySource):
    """Find companies where founders are publicly active."""

    @property
    def name(self) -> str:
        return "founder_activity"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        companies: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            "Indian D2C founder interview 2026",
            "India startup founder story D2C brand 2026",
            "Indian ecommerce founder journey 2026",
            "India D2C brand founder background 2026",
            "Indian D2C entrepreneur founder led brand 2026",
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

                # Look for founder names: "X, Founder of Y" or "X founded Y"
                founder_patterns = [
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:Founder|Co-Founder|CEO|founder|co-founder|ceo)\s+(?:of|at)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:,|\.|and|who|that|which|$))',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:founded|co-founded|started|launched)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:in|in|with|to|,|\.|$))',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:is|was)\s+(?:the\s+)?(?:Founder|Co-Founder|CEO)\s+(?:of|at)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:,|\.|and|who|$))',
                ]

                for pattern in founder_patterns:
                    matches = re.findall(pattern, excerpt_text + " " + title)
                    for founder_name, company_name in matches:
                        founder_name = founder_name.strip()
                        company_name = company_name.strip()
                        company_name = company_name.strip(".,;:!?\"'")

                        if len(company_name) < 3 or len(company_name) > 50:
                            continue
                        if len(founder_name) < 3 or len(founder_name) > 40:
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
                            source="founder_activity",
                            discovery_reason=f"Founder {founder_name} publicly active",
                            discovery_date=date.today(),
                            business_stage="growing",
                            founder_name=founder_name,
                            founder_role="Founder",
                            founder_source=url,
                            founder_confidence=0.8,
                            growth_signals=[f"Founder publicly identifiable: {founder_name}"],
                            growth_signal_sources=[url],
                            metadata={
                                "founder_name": founder_name,
                                "article_url": url,
                                "query": query,
                            },
                        )
                        companies.append(company)
                        logger.info("  DISCOVERED: %s — Founder: %s", company_name, founder_name)

        return companies[:limit]

    def _guess_domain(self, company_name: str) -> str:
        base = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        base = re.sub(r'\s+', '', base)
        return f"{base}.com"
