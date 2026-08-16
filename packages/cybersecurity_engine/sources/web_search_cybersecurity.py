"""Web Search Cybersecurity Collector — Finds buying signals via web search."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from urllib.parse import unquote

import httpx

from cybersecurity_engine.sources import BaseCybersecurityCollector, RawSignal

logger = logging.getLogger(__name__)

# Search queries for direct buying evidence (less restrictive - no exact quotes)
BUYING_SEARCH_QUERIES = [
    # Direct buying requests (broadened)
    "looking for penetration testing company",
    "need penetration testing",
    "need VAPT",
    "need vulnerability assessment",
    "need security audit",
    "looking for cybersecurity company",
    "need external security testing",
    "need web application penetration testing",
    "need API security testing",
    "need mobile application security testing",
    "need cloud security assessment",
    "need network penetration testing",
    "need security testing for SOC 2",
    "need security testing for ISO 27001",
    "enterprise customer requires penetration testing",
    "customer requires security assessment",
    "looking for security testing vendor",
    "looking for ethical hackers",
    "looking for security testing team",
    # Procurement signals (broadened)
    "security testing RFP",
    "penetration testing RFP",
    "security assessment tender",
    "security audit procurement",
    # Broader buying intent
    "hire penetration testing",
    "contract security testing",
    "security testing company",
    "penetration testing firm",
    "security consulting firm",
]

# Pain signal queries (broadened)
PAIN_SEARCH_QUERIES = [
    "discovered vulnerability need remediation",
    "security incident need help",
    "data breach need security",
    "failed security audit need vendor",
    "compliance deadline security testing",
    "SOC 2 penetration testing requirement",
    "ISO 27001 security assessment deadline",
    "enterprise customer security testing requirement",
    "security gap need assessment",
    "compliance pressure security audit",
]

# Additional broader queries for more coverage
BROADER_QUERIES = [
    "penetration testing services",
    "VAPT services company",
    "security assessment services",
    "cybersecurity consulting services",
    "web application security testing",
    "cloud security assessment services",
]


class WebSearchCybersecurityCollector(BaseCybersecurityCollector):
    """Collects cybersecurity buying signals via web search."""

    source_name = "web_search"
    source_tier = 2

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        max_items: int = 50,
    ) -> None:
        super().__init__(http_client)
        self.max_items = max_items

    async def collect(self) -> Sequence[RawSignal]:
        """Collect cybersecurity signals via web search."""
        all_signals: list[RawSignal] = []
        seen_urls: set[str] = set()

        # Combine all query sets
        all_queries = BUYING_SEARCH_QUERIES + PAIN_SEARCH_QUERIES + BROADER_QUERIES

        for query in all_queries:
            try:
                signals = await self._duckduckgo_search(query)
                for signal in signals:
                    if signal.url not in seen_urls:
                        seen_urls.add(signal.url)
                        all_signals.append(signal)
                # Delay between queries to avoid rate limiting
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.warning("Web search failed for query '%s': %s", query, e)
                continue

        all_signals.sort(key=lambda s: s.score, reverse=True)
        logger.info("WebSearch collector found %d signals total", len(all_signals))
        return all_signals[: self.max_items]

    async def _duckduckgo_search(self, query: str) -> list[RawSignal]:
        """Search DuckDuckGo for a query with retry logic."""
        signals = []
        max_retries = 2

        for attempt in range(max_retries):
            try:
                response = await self.http_client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query, "kl": "us-en"},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                    timeout=15.0,
                    follow_redirects=True,
                )
                if response.status_code == 429:
                    logger.warning("DuckDuckGo rate limited (attempt %d/%d)", attempt + 1, max_retries)
                    await asyncio.sleep(3.0 * (attempt + 1))
                    continue
                if response.status_code == 403:
                    logger.debug("DuckDuckGo returned 403 (attempt %d/%d)", attempt + 1, max_retries)
                    await asyncio.sleep(2.0)
                    continue
                response.raise_for_status()
                html = response.text

                # Parse results from HTML
                results = self._parse_ddg_results(html)

                for result in results:
                    score = self._calculate_score(result.get("snippet", ""), result.get("title", ""))
                    signals.append(RawSignal(
                        source="web_search",
                        source_tier=self.source_tier,
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        content=result.get("snippet", ""),
                        score=score,
                        metadata={
                            "query": query,
                            "search_engine": "duckduckgo",
                        },
                    ))
                return signals
            except httpx.RequestError as e:
                logger.debug(
                    "DuckDuckGo request failed (attempt %d/%d): %s",
                    attempt + 1, max_retries, e,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0)
            except Exception as e:
                logger.debug(
                    "DuckDuckGo search failed (attempt %d/%d): %s",
                    attempt + 1, max_retries, e,
                )
                return []

        return signals

    def _parse_ddg_results(self, html: str) -> list[dict[str, str]]:
        """Parse DuckDuckGo HTML results with multiple parsing strategies."""
        results = []

        # Strategy 1: Standard result__a pattern
        result_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL
        )

        for match in result_pattern.finditer(html):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()

            # Clean DDG redirect URLs
            if "uddg=" in url:
                url_match = re.search(r'uddg=([^&]+)', url)
                if url_match:
                    url = unquote(url_match.group(1))

            if url.startswith("http") and title:
                results.append({
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                })

        # Strategy 2: Fallback - look for any result links
        if not results:
            fallback_pattern = re.compile(
                r'<a[^>]+href="(https?://[^"]*)"[^>]*>(.*?)</a>',
                re.DOTALL
            )
            for match in fallback_pattern.finditer(html):
                url = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()

                # Skip DDG internal links
                if "duckduckgo.com" in url or not title:
                    continue

                # Clean DDG redirect URLs
                if "uddg=" in url:
                    url_match = re.search(r'uddg=([^&]+)', url)
                    if url_match:
                        url = unquote(url_match.group(1))

                if url.startswith("http") and title and len(title) > 5:
                    results.append({
                        "url": url,
                        "title": title,
                        "snippet": "",
                    })

        return results

    def _calculate_score(self, text: str, title: str) -> int:
        """Calculate relevance score."""
        full_text = f"{title} {text}".lower()
        score = 0

        # Direct buying signals (highest priority)
        direct_keywords = [
            "looking for penetration testing", "need penetration testing",
            "need vapt", "need vulnerability assessment", "need security audit",
            "looking for cybersecurity", "need external security",
            "security testing rfp", "penetration testing rfp",
            "enterprise customer requires", "customer requires security",
            "hire penetration testing", "contract security testing",
            "penetration testing firm", "security consulting firm",
        ]
        for kw in direct_keywords:
            if kw in full_text:
                score += 15

        # Strong signals
        strong_keywords = [
            "penetration test", "pentest", "vapt", "security audit",
            "vulnerability assessment", "security testing", "security assessment",
            "rfp", "tender", "procurement", "security firm", "security company",
            "security provider", "security vendor",
        ]
        for kw in strong_keywords:
            if kw in full_text:
                score += 5

        # Compliance signals
        compliance_keywords = [
            "soc 2", "soc2", "iso 27001", "pci dss", "hipaa", "gdpr",
            "compliance", "certification", "security compliance",
        ]
        for kw in compliance_keywords:
            if kw in full_text:
                score += 3

        # Pain signal keywords
        pain_keywords = [
            "security gap", "security hole", "security weakness",
            "compliance deadline", "audit deadline", "failed compliance",
            "security concern", "security risk", "data breach",
            "security incident", "vulnerability found",
        ]
        for kw in pain_keywords:
            if kw in full_text:
                score += 3

        return score
