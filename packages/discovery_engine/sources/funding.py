"""Discover companies through recent funding announcements."""

from __future__ import annotations

import re
import logging
from datetime import date

from packages.discovery_engine.base import DiscoverySource
from packages.discovery_engine.models import DiscoveredCompany

logger = logging.getLogger(__name__)


class FundingDiscovery(DiscoverySource):
    """Find companies that recently raised funding."""

    @property
    def name(self) -> str:
        return "funding_announcements"

    async def discover(self, limit: int = 50) -> list[DiscoveredCompany]:
        # Import websearch here to avoid circular imports at module level
        from opencode.tools import websearch

        companies: list[DiscoveredCompany] = []
        seen: set[str] = set()

        queries = [
            "Indian D2C startup funding 2026",
            "India D2C brand raised funding 2026",
            "Indian ecommerce startup Series A funding 2026",
            "India direct to consumer brand funding round 2026",
            "Indian D2C beauty fashion food startup raised 2026",
            "India new age brand funding pre-series A 2026",
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

                # Extract company names from funding articles
                # Pattern: "Company raises Rs X crore" or "Company raised $X million"
                funding_patterns = [
                    r'(?:raises?|raised|securing|secures?|closes?|closed)\s+(?:Rs\.?\s*[\d,.]+\s*(?:crore|lakh|Cr)|\$[\d,.]+\s*(?:million|M|billion|B))',
                ]

                # Look for company names near funding mentions
                # Common pattern: "[Company Name] raises Rs X crore from [Investor]"
                company_matches = re.findall(
                    r'([A-Z][A-Za-z\s&\'\.]+?)\s+(?:raises?|raised|secures?|closes?|closed|gets?|getting)\s+(?:Rs\.?\s*[\d,.]+\s*(?:crore|lakh|Cr)|\$[\d,.]+\s*(?:million|M|billion|B))',
                    excerpt_text + " " + title,
                )

                if not company_matches:
                    # Try reverse pattern: "Funding for Company Name"
                    company_matches = re.findall(
                        r'(?:for|into|to)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:in|at|from|with|via|through|round|series|pre))',
                        excerpt_text + " " + title,
                    )

                for match in company_matches:
                    company_name = match.strip()
                    # Clean up
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = company_name.strip(".,;:!?\"'")

                    # Skip if too short, too long, or looks like a non-company
                    if len(company_name) < 3 or len(company_name) > 50:
                        continue
                    if company_name.lower() in seen:
                        continue
                    # Skip common false positives
                    skip_words = [
                        "the", "this", "that", "from", "with", "into", "through",
                        "india", "indian", "d2c", "startup", "brand", "company",
                        "funding", "venture", "capital", "partners", "group",
                        "series", "round", "raised", "raises", "funding",
                    ]
                    if company_name.lower().split()[0] in skip_words:
                        continue

                    seen.add(company_name.lower())

                    # Extract funding amount
                    amount_match = re.search(
                        r'(?:Rs\.?\s*([\d,.]+)\s*crore|(\$[\d,.]+)\s*(?:million|M))',
                        excerpt_text + " " + title,
                    )
                    amount = ""
                    if amount_match:
                        if amount_match.group(1):
                            amount = f"Rs {amount_match.group(1)} Cr"
                        elif amount_match.group(2):
                            amount = f"{amount_match.group(2)}M"

                    # Extract investor
                    investor_match = re.search(
                        r'(?:led by|from|participation from|invested by)\s+([A-Z][A-Za-z\s&\'\.]+?)(?:\s+(?:and|with|,|\.|$))',
                        excerpt_text,
                    )
                    investor = investor_match.group(1).strip() if investor_match else ""

                    # Guess domain from company name
                    domain_guess = self._guess_domain(company_name)

                    discovery_reason = f"Raised {amount} funding" if amount else "Raised funding"
                    if investor:
                        discovery_reason += f" from {investor}"

                    company = DiscoveredCompany(
                        company_name=company_name,
                        domain=domain_guess,
                        source="funding_announcements",
                        discovery_reason=discovery_reason,
                        discovery_date=date.today(),
                        business_stage="growing",
                        buying_signals=[f"Raised {amount} in funding" if amount else "Recent funding round"],
                        buying_signal_sources=[url],
                        metadata={
                            "funding_amount": amount,
                            "investor": investor,
                            "article_url": url,
                            "query": query,
                        },
                    )
                    companies.append(company)
                    logger.info("  DISCOVERED: %s — %s", company_name, discovery_reason)

        return companies[:limit]

    def _guess_domain(self, company_name: str) -> str:
        """Guess domain from company name."""
        # Remove special characters, lowercase, join
        base = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        base = re.sub(r'\s+', '', base)
        return f"{base}.com"
