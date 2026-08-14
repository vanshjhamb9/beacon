"""Shopify store collector for Indian ecommerce businesses."""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator
from urllib.parse import urlparse

import httpx

from packages.ecommerce_leads.models import RawEcommerceLead

logger = logging.getLogger(__name__)

SHOPIFY_INDIA_KEYWORDS = [
    "shopify india",
    "indian shopify store",
    "shopify store india",
    "india d2c brand shopify",
]

SHOPIFY_THEME_PATTERNS = [
    re.compile(r"cdn\.shopify\.com"),
    re.compile(r"Shopify\.theme", re.IGNORECASE),
    re.compile(r"shopify-section", re.IGNORECASE),
    re.compile(r"shopify-payment-button", re.IGNORECASE),
]

SHOPIFY_JSON_INDICATORS = [
    "/products.json",
    "/collections.json",
    "/meta.json",
]

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
    "Surat", "Kanpur", "Nagpur", "Indore", "Bhopal",
    "Visakhapatnam", "Patna", "Vadodara", "Ghaziabad", "Ludhiana",
]

INDIAN_STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
    "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh",
    "Andhra Pradesh", "Bihar", "Punjab", "Haryana", "Kerala",
]


class ShopifyCollector:
    """Collects Shopify stores from India."""

    def __init__(self, *, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def collect_from_domains(
        self, domains: list[str]
    ) -> AsyncIterator[RawEcommerceLead]:
        """Check a list of domains for Shopify stores."""
        async with httpx.AsyncClient(
            timeout=self.timeout, headers=self._headers, follow_redirects=True
        ) as client:
            for domain in domains:
                try:
                    lead = await self._probe_shopify(client, domain)
                    if lead:
                        yield lead
                except Exception:
                    logger.debug("Failed to probe %s", domain)

    async def _probe_shopify(
        self, client: httpx.AsyncClient, domain: str
    ) -> RawEcommerceLead | None:
        """Probe a domain to check if it's a Shopify store."""
        url = f"https://{domain}"
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None

            body = resp.text
            is_shopify = any(p.search(body) for p in SHOPIFY_THEME_PATTERNS)

            if not is_shopify:
                return None

            title_match = re.search(r"<title>(.*?)</title>", body, re.IGNORECASE)
            store_name = title_match.group(1).strip() if title_match else domain

            product_count = await self._get_product_count(client, url)

            return RawEcommerceLead(
                company_name=store_name,
                website=url,
                domain=domain,
                platform="shopify",
                country="India",
                product_count=product_count,
                source="shopify_collector",
                source_url=url,
                metadata={"probe_method": "theme_detection"},
            )
        except httpx.RequestError:
            return None

    async def _get_product_count(
        self, client: httpx.AsyncClient, base_url: str
    ) -> int:
        """Try to get product count from Shopify JSON API."""
        try:
            resp = await client.get(f"{base_url}/products.json?limit=1")
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("products", [])
                if products:
                    return len(products)
        except Exception:
            pass
        return 0

    async def collect_shopify_directories(
        self, limit: int = 500
    ) -> AsyncIterator[RawEcommerceLead]:
        """Collect from known Shopify store directories and lists."""
        known_shopify_india_domains = [
            "mamaearth.in",
            "wowskinscience.com",
            "plumgoodness.com",
            "theomancompany.com",
            "beardo.in",
            "mcaffeine.com",
            "thesouledstore.com",
            "bewakoof.com",
            "crazydomains.in",
            "boat-lifestyle.com",
            "noise.tech",
            "fireboltt.com",
            "ptron.com",
            "ambraneindia.com",
            "lapguard.in",
            "syska.com",
            "philips.co.in",
            "hamleys.com",
            "toybasket.in",
            "firstcry.com",
            "hopscotch.in",
            "babyoye.com",
            "myntra.com",
            "ajio.com",
            "nykaa.com",
            "purplle.com",
            "beautybay.com",
            "colorbarcosmetics.com",
            "sugarcosmetics.com",
            "florence by mills.com",
            "lakmeindia.com",
            "forestessentialsindia.com",
            "khadinatural.com",
            "rusticart.in",
            "biomaee.in",
            "juicychemistry.com",
            "dermaessentia.com",
            "dermaco.in",
            "minimalist.ind.in",
            "deconstruct.in",
            "pilgrim.in",
            "dotkey.in",
            "aromaplane.com",
            "bombayshavingcompany.com",
            "theskinstory.in",
            "chemistatplay.com",
            "briluce.com",
            "snitch.co.in",
            "thesouledstore.com",
            "bewakoof.com",
            "berrylush.com",
            "libas.in",
            "wrayandnephew.com",
            "jaipurrugs.co.in",
            "pepperfry.com",
            "urbanladder.com",
            "godrejinterio.com",
            "homecentre.com",
            "livspace.com",
            "craftsvilla.com",
            "jaypore.com",
            "okhai.org",
            "nicobar.com",
            "goodearth.in",
            "thevasa.com",
            "mohanchair.com",
            "nativecircle.com",
            "indiacircus.com",
            "spacejoy.com",
            "addresshome.com",
            "bajajfinservmarkets.in",
            "cromaretail.com",
            "tatacliq.com",
            "reliancedigital.in",
            "vijaysales.com",
            "croma.com",
            "flipkart.com",
            "snapdeal.com",
            "paytmmall.com",
            "jioMart.com",
            "bigbasket.com",
            "grofers.com",
            "blinkit.com",
            "zeptonow.com",
            "instamart.com",
            "dmart.in",
            "reliancefresh.com",
            "moreatbigbazaar.com",
            " Spencer's",
            "naturebasket.co.in",
            "ezpz.in",
            "organicmandi.in",
            "farmfresh.co.in",
            "iomato.com",
            "freshmenu.com",
            "box8.in",
            "faasos.com",
            "swiggy.com",
            "zomato.com",
        ]

        async with httpx.AsyncClient(
            timeout=self.timeout, headers=self._headers, follow_redirects=True
        ) as client:
            count = 0
            for domain in known_shopify_india_domains:
                if count >= limit:
                    break
                domain = domain.strip()
                if not domain:
                    continue
                try:
                    lead = await self._probe_shopify(client, domain)
                    if lead:
                        count += 1
                        yield lead
                except Exception:
                    logger.debug("Failed to probe %s", domain)
