"""Web collector for discovering Indian ecommerce businesses."""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator
from urllib.parse import quote_plus, urlparse

import httpx

from packages.ecommerce_leads.models import RawEcommerceLead

logger = logging.getLogger(__name__)

INDIA_ECOMMERCE_KEYWORDS = [
    "buy online india",
    "indian d2c brands",
    "online store india",
    "indian fashion brand online",
    "indian skincare brand",
    "indian cosmetics brand",
    "indian supplement brand",
    "indian home decor online",
    "indian electronics store",
    "shopify india store",
    "indian ecommerce brand",
    "d2c brand india",
    "indian beauty brand",
    "indian wellness brand",
    "indian organic brand",
    "indian clothing brand online",
    "indian jewellery online",
    "indian toy store",
    "indian pet store",
    "indian grocery online",
]

INDIA_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
    "Surat", "Kanpur", "Nagpur", "Indore", "Bhopal",
]

BUSINESS_DIRECTORIES = [
    "https://www.indiamart.com",
    "https://www.tradeindia.com",
    "https://www.exportersindia.com",
]

ECOMMERCE_LIST_URLS = [
    "https://www.shopify.com/blog/indian-ecommerce-brands",
    "https://economictimes.indiatimes.com/tech/startups",
]


class WebCollector:
    """Discover Indian ecommerce businesses from web sources."""

    def __init__(self, *, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def collect_from_search(
        self, keywords: list[str] | None = None, limit: int = 500
    ) -> AsyncIterator[RawEcommerceLead]:
        """Discover ecommerce businesses using search-engine style queries."""
        if keywords is None:
            keywords = INDIA_ECOMMERCE_KEYWORDS

        async with httpx.AsyncClient(
            timeout=self.timeout, headers=self._headers, follow_redirects=True
        ) as client:
            count = 0
            for keyword in keywords:
                if count >= limit:
                    break
                async for lead in self._search_keyword(client, keyword, limit - count):
                    count += 1
                    yield lead

    async def _search_keyword(
        self, client: httpx.AsyncClient, keyword: str, remaining: int
    ) -> AsyncIterator[RawEcommerceLead]:
        """Simulate search results extraction for a keyword."""
        search_queries = self._build_search_variations(keyword)
        for query in search_queries[:5]:
            try:
                results = await self._extract_from_search_page(client, query)
                for result in results[:remaining]:
                    yield result
            except Exception:
                logger.debug("Search failed for query: %s", query)

    def _build_search_variations(self, keyword: str) -> list[str]:
        """Build search query variations from a base keyword."""
        variations = [
            keyword,
            f"{keyword} site:shopify.com",
            f"{keyword} buy online",
            f"best {keyword}",
            f"top {keyword} brands",
        ]
        return variations

    async def _extract_from_search_page(
        self, client: httpx.AsyncClient, query: str
    ) -> list[RawEcommerceLead]:
        """Extract ecommerce leads from a search-like page."""
        leads: list[RawEcommerceLead] = []
        encoded = quote_plus(query)
        urls_to_try = [
            f"https://html.duckduckgo.com/html/?q={encoded}",
        ]

        for search_url in urls_to_try:
            try:
                resp = await client.get(search_url)
                if resp.status_code != 200:
                    continue

                body = resp.text
                urls = self._extract_urls_from_html(body)

                for url in urls:
                    domain = urlparse(url).netloc.removeprefix("www.")
                    if not domain or not self._is_indian_domain(domain):
                        continue

                    lead = RawEcommerceLead(
                        company_name=self._guess_company_name(domain),
                        website=url,
                        domain=domain,
                        country="India",
                        source="web_collector",
                        source_url=search_url,
                        metadata={"query": query},
                    )
                    leads.append(lead)
            except Exception:
                continue

        return leads

    def _extract_urls_from_html(self, html: str) -> list[str]:
        """Extract URLs from HTML content."""
        url_pattern = re.compile(r'href="(https?://[^"]+)"')
        urls = url_pattern.findall(html)
        cleaned: list[str] = []
        seen: set[str] = set()
        for url in urls:
            url = url.split("?")[0].split("#")[0]
            if url not in seen and "duckduckgo" not in url:
                seen.add(url)
                cleaned.append(url)
        return cleaned[:50]

    def _is_indian_domain(self, domain: str) -> bool:
        """Check if domain appears to be Indian."""
        indian_tlds = [".in", ".co.in", ".com.in"]
        for tld in indian_tlds:
            if domain.endswith(tld):
                return True

        indian_keywords = [
            "india", "indian", "mumbai", "delhi", "bangalore",
            "shopify", "d2c", "ecommerce",
        ]
        return any(kw in domain.lower() for kw in indian_keywords)

    def _guess_company_name(self, domain: str) -> str:
        """Guess a company name from the domain."""
        name = domain.split(".")[0]
        name = name.replace("-", " ").replace("_", " ")
        return name.title()

    async def collect_from_lists(
        self, urls: list[str] | None = None, limit: int = 500
    ) -> AsyncIterator[RawEcommerceLead]:
        """Collect from curated lists of Indian ecommerce stores."""
        if urls is None:
            urls = ECOMMERCE_LIST_URLS

        async with httpx.AsyncClient(
            timeout=self.timeout, headers=self._headers, follow_redirects=True
        ) as client:
            count = 0
            for list_url in urls:
                if count >= limit:
                    break
                try:
                    resp = await client.get(list_url)
                    if resp.status_code != 200:
                        continue

                    body = resp.text
                    urls_found = self._extract_urls_from_html(body)

                    for url in urls_found:
                        if count >= limit:
                            break
                        domain = urlparse(url).netloc.removeprefix("www.")
                        if domain and self._is_indian_domain(domain):
                            lead = RawEcommerceLead(
                                company_name=self._guess_company_name(domain),
                                website=url,
                                domain=domain,
                                country="India",
                                source="web_collector_list",
                                source_url=list_url,
                            )
                            count += 1
                            yield lead
                except Exception:
                    logger.debug("Failed to fetch list: %s", list_url)

    async def collect_uknown_shopify_stores(
        self, limit: int = 500
    ) -> AsyncIterator[RawEcommerceLead]:
        """Collect from curated known Indian Shopify/D2C stores."""
        known_stores = [
            ("mamaearth.in", "Mamaearth", "beauty"),
            ("beardo.in", "Beardo", "grooming"),
            ("mcaffeine.com", "mCaffeine", "skincare"),
            ("wowskinscience.com", "WOW Skin Science", "skincare"),
            ("plumgoodness.com", "Plum Goodness", "beauty"),
            ("sugarcosmetics.com", "Sugar Cosmetics", "cosmetics"),
            ("nykaa.com", "Nykaa", "beauty marketplace"),
            ("purplle.com", "Purplle", "beauty marketplace"),
            ("boat-lifestyle.com", "boAt", "electronics"),
            ("noise.tech", "Noise", "electronics"),
            ("fireboltt.com", "Fire-Boltt", "electronics"),
            ("thesouledstore.com", "The Souled Store", "fashion"),
            ("bewakoof.com", "Bewakoof", "fashion"),
            ("snitch.co.in", "Snitch", "fashion"),
            ("berrylush.com", "Berrylush", "fashion"),
            ("libas.in", "Libas", "fashion"),
            ("pepperfry.com", "Pepperfry", "furniture"),
            ("urbanladder.com", "Urban Ladder", "furniture"),
            ("fabindia.com", "Fabindia", "lifestyle"),
            ("jaypore.com", "Jaypore", "lifestyle"),
            ("nicobar.com", "Nicobar", "lifestyle"),
            ("okhai.org", "Okhai", "handicrafts"),
            ("firstcry.com", "FirstCry", "kids"),
            ("hopscotch.in", "Hopscotch", "kids"),
            ("bigbasket.com", "BigBasket", "grocery"),
            ("zeptonow.com", "Zepto", "quick commerce"),
            ("blinkit.com", "Blinkit", "quick commerce"),
            ("dmart.in", "DMart", "retail"),
            ("tatacliq.com", "Tata CLiQ", "marketplace"),
            ("reliancedigital.in", "Reliance Digital", "electronics"),
            ("croma.com", "Croma", "electronics"),
            ("vijaysales.com", "Vijay Sales", "electronics"),
            ("lakmeindia.com", "Lakme", "beauty"),
            ("forestessentialsindia.com", "Forest Essentials", "luxury beauty"),
            ("khadinatural.com", "Khadi Natural", "natural products"),
            ("juicychemistry.com", "Juicy Chemistry", "organic beauty"),
            ("minimalist.ind.in", "Minimalist", "skincare"),
            ("pilgrim.in", "Pilgrim", "skincare"),
            ("dotkey.in", "Dot Key", "skincare"),
            ("dermaco.in", "Derma Co", "skincare"),
            ("chemistatplay.com", "Chemist at Play", "skincare"),
            ("bombayshavingcompany.com", "Bombay Shaving Company", "grooming"),
            ("theomancompany.com", "The Man Company", "grooming"),
            ("crazydomains.in", "Crazydomains", "domains"),
            ("syska.com", "Syska", "electronics"),
            ("ambraneindia.com", "Ambrane", "electronics"),
            ("ptron.com", "pTron", "electronics"),
            ("craftsvilla.com", "CraftsVilla", "handicrafts"),
            ("addresshome.com", "Address Home", "home decor"),
            ("spacejoy.com", "SpaceJoy", "interior design"),
            ("homecentre.com", "Home Centre", "home decor"),
            ("godrejinterio.com", "Godrej Interio", "furniture"),
            ("hamleys.com", "Hamleys", "toys"),
            ("roastea.com", "Roastea", "tea/coffee"),
            ("chaiology.in", "Chaiology", "tea"),
            ("teabox.com", "Teabox", "tea"),
            ("rawpressery.com", "Raw Pressery", "beverages"),
            ("box8.in", "BOX8", "food"),
            ("freshmenu.com", "FreshMenu", "food"),
            ("iomato.com", "iMato", "food"),
            ("organicmandi.in", "Organic Mandi", "organic food"),
            ("naturebasket.co.in", "Nature's Basket", "gourmet food"),
            ("petbarn.in", "Pet Barn", "pet supplies"),
            ("headsupfortails.com", "Heads Up For Tails", "pet supplies"),
            ("zoivapets.com", "Zoiva", "pet supplies"),
            ("rusticart.in", "Rustic Art", "personal care"),
            ("biomaee.in", "Biomaee", "wellness"),
            ("deconstruct.in", "Deconstruct", "skincare"),
            ("theskinstory.in", "The Skin Story", "skincare"),
            ("briluce.com", "Briluce", "jewellery"),
            ("caratlane.com", "CaratLane", "jewellery"),
            ("titan.co.in", "Titan", "jewellery/watches"),
            ("kalyanjewellers.net", "Kalyan Jewellers", "jewellery"),
            ("tanishq.co.in", "Tanishq", "jewellery"),
            ("bluestone.com", "BlueStone", "jewellery"),
            ("pipabella.com", "Pipa Bella", "fashion jewellery"),
            ("thevazono.com", "The VaZoNo", "fashion"),
            ("clabel.in", "C Label", "fashion"),
            ("snitch.co.in", "Snitch", "mens fashion"),
            ("louisphilippe.com", "Louis Philippe", "mens fashion"),
            ("allensolly.com", "Allen Solly", "fashion"),
            ("peterengland.com", "Peter England", "fashion"),
            ("arrow.com", "Arrow", "formal wear"),
            ("johnplayers.com", "John Players", "fashion"),
            ("vanheusen.com", "Van Heusen", "fashion"),
            ("parkavenue.in", "Park Avenue", "mens fashion"),
            ("wooplr.com", "Wooplr", "fashion marketplace"),
            ("stalkbuylove.com", "StalkBuyLove", "fashion"),
            ("koovs.com", "Koovs", "fashion"),
            ("ajio.com", "AJIO", "fashion marketplace"),
            ("myntra.com", "Myntra", "fashion marketplace"),
            ("jabong.com", "Jabong", "fashion marketplace"),
        ]

        async with httpx.AsyncClient(
            timeout=self.timeout, headers=self._headers, follow_redirects=True
        ) as client:
            count = 0
            for domain, name, category in known_stores:
                if count >= limit:
                    break
                domain = domain.strip()
                if not domain:
                    continue
                url = f"https://{domain}"
                try:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        final_domain = urlparse(str(resp.url)).netloc.removeprefix("www.")
                        lead = RawEcommerceLead(
                            company_name=name,
                            website=str(resp.url),
                            domain=final_domain or domain,
                            category=category,
                            country="India",
                            source="known_store_list",
                            source_url=url,
                        )
                        count += 1
                        yield lead
                except Exception:
                    continue
