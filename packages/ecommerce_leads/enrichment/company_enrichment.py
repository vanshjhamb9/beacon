"""Company enrichment for ecommerce leads."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from packages.ecommerce_leads.models import EnrichedEcommerceLead, RawEcommerceLead

logger = logging.getLogger(__name__)


class CompanyEnricher:
    """Enrich company data from website scraping."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def enrich(self, lead: EnrichedEcommerceLead) -> EnrichedEcommerceLead:
        """Enrich company information from the website."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=self._headers, follow_redirects=True
            ) as client:
                await self._enrich_about(client, lead)
                await self._enrich_products(client, lead)
                await self._enrich_meta(client, lead)
                self._detect_city_state(lead)
        except Exception:
            logger.debug("Company enrichment failed for %s", lead.raw.website)

        return lead

    async def _enrich_about(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Scrape about page for company description."""
        about_urls = [
            f"{lead.raw.website}/about",
            f"{lead.raw.website}/about-us",
            f"{lead.raw.website}/pages/about-us",
            f"{lead.raw.website}/pages/about",
            f"{lead.raw.website}/our-story",
        ]

        for url in about_urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    body = resp.text
                    desc = self._extract_meta_description(body)
                    if desc:
                        lead.raw.description = desc
                        break

                    og_desc = self._extract_og_field(body, "og:description")
                    if og_desc:
                        lead.raw.description = og_desc
                        break
            except Exception:
                continue

    async def _enrich_products(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Count products from shop pages."""
        product_urls = [
            f"{lead.raw.website}/products.json?limit=1",
            f"{lead.raw.website}/collections/all/products.json?limit=1",
            f"{lead.raw.website}/products",
            f"{lead.raw.website}/collections/all",
        ]

        for url in product_urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    if ".json" in url:
                        data = resp.json()
                        products = data.get("products", [])
                        if products:
                            lead.raw.product_count = max(lead.raw.product_count, len(products))
                            return
                    else:
                        count = self._count_products_from_html(resp.text)
                        if count > 0:
                            lead.raw.product_count = max(lead.raw.product_count, count)
                            return
            except Exception:
                continue

    async def _enrich_meta(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Extract meta tags for enrichment."""
        try:
            resp = await client.get(lead.raw.website)
            if resp.status_code == 200:
                body = resp.text
                if not lead.raw.description:
                    desc = self._extract_meta_description(body)
                    if desc:
                        lead.raw.description = desc

                title = self._extract_title(body)
                if title and not lead.raw.company_name:
                    lead.raw.company_name = title
        except Exception:
            pass

    def _extract_meta_description(self, html: str) -> str:
        match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        match = re.search(
            r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return ""

    def _extract_og_field(self, html: str, field: str) -> str:
        match = re.search(
            rf'<meta\s+property=["\']{field}["\']\s+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return ""

    def _extract_title(self, html: str) -> str:
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _count_products_from_html(self, html: str) -> int:
        product_indicators = [
            re.compile(r'product-card', re.IGNORECASE),
            re.compile(r'product-item', re.IGNORECASE),
            re.compile(r'grid-item', re.IGNORECASE),
            re.compile(r'product-grid', re.IGNORECASE),
        ]
        count = 0
        for pattern in product_indicators:
            count += len(pattern.findall(html))
        return count

    def _detect_city_state(self, lead: EnrichedEcommerceLead) -> None:
        """Try to detect city/state from the domain or description."""
        text = f"{lead.raw.domain} {lead.raw.description}".lower()

        city_state_map = {
            "mumbai": ("Mumbai", "Maharashtra"),
            "bangalore": ("Bangalore", "Karnataka"),
            "bengaluru": ("Bangalore", "Karnataka"),
            "delhi": ("Delhi", "Delhi"),
            "new delhi": ("New Delhi", "Delhi"),
            "hyderabad": ("Hyderabad", "Telangana"),
            "chennai": ("Chennai", "Tamil Nadu"),
            "pune": ("Pune", "Maharashtra"),
            "kolkata": ("Kolkata", "West Bengal"),
            "ahmedabad": ("Ahmedabad", "Gujarat"),
            "jaipur": ("Jaipur", "Rajasthan"),
            "lucknow": ("Lucknow", "Uttar Pradesh"),
        }

        for keyword, (city, state) in city_state_map.items():
            if keyword in text:
                lead.raw.city = city
                lead.raw.state = state
                break
