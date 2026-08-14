"""Discover companies through accelerator/incubator programs."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class AcceleratorDiscovery(DiscoverySource):
    """Find companies backed by accelerators or incubators."""

    @property
    def name(self) -> str:
        return "accelerator_incubator"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        from opencode.tools import websearch

        companies: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            "India D2C accelerator batch 2025 2026",
            "Indian startup incubator cohort D2C ecommerce 2026",
            "India D2C brand accelerator program selected 2026",
            "Indian ecommerce startup incubator batch 2026",
            "India D2C founder accelerator graduation 2026",
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

                # Look for company names in accelerator context
                accel_patterns = [
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:selected|chosen|picked|joins?|joined|graduates?|graduated|completes?|completed)',
                    r'(?:batch|cohort|program)\s+(?:of|includes?|features?|includes?)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:and|,|\.|among))',
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:among|one of|part of)\s+(?:the|a)\s+(?:selected|chosen|picked)',
                ]

                company_matches = []
                for pattern in accel_patterns:
                    matches = re.findall(pattern, excerpt_text + " " + title)
                    company_matches.extend(matches)

                # Also look for accelerator names to tag
                accel_name = ""
                accel_match = re.search(
                    r'(?:at|from|by|through)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:accelerator|incubator|program|batch|cohort))',
                    excerpt_text,
                )
                if accel_match:
                    accel_name = accel_match.group(1).strip()

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

                    reason = f"Part of {accel_name} accelerator" if accel_name else "Selected for accelerator program"

                    domain_guess = self._guess_domain(company_name)

                    company = DiscoveredCompany(
                        company_name=company_name,
                        domain=domain_guess,
                        source="accelerator_incubator",
                        discovery_reason=reason,
                        discovery_date=date.today(),
                        business_stage="early",
                        growth_signals=[reason],
                        growth_signal_sources=[url],
                        metadata={
                            "accelerator": accel_name,
                            "article_url": url,
                            "query": query,
                        },
                    )
                    companies.append(company)
                    logger.info("  DISCOVERED: %s — %s", company_name, reason)

        return companies[:limit]

    def _guess_domain(self, company_name: str) -> str:
        base = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        base = re.sub(r'\s+', '', base)
        return f"{base}.com"
