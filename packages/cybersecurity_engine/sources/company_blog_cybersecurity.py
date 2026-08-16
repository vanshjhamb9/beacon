"""Company Blog Cybersecurity Collector — Detects security announcements from company sites."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from cybersecurity_engine.sources import BaseCybersecurityCollector, RawSignal

logger = logging.getLogger(__name__)


# Security announcement patterns on company blogs
SECURITY_BLOG_PATTERNS = [
    # Security page patterns
    r"(?:/security|/trust|/compliance|/privacy|/status)(?:/|$)",
    # Blog post patterns
    r"(?:/blog|/news|/articles|/posts)/(?:.*?(?:security|vulnerability|compliance|audit|incident|breach))",
]

# Content patterns that indicate security announcements (broadened)
SECURITY_CONTENT_PATTERNS = [
    r"(?:we|our)\s+(?:have?|has)?\s+(?:completed|passed|undergone|finished)\s+(?:a\s+)?(?:penetration\s+test|security\s+audit|security\s+assessment|vulnerability\s+assessment)",
    r"(?:we|our)\s+(?:have?|has)?\s+(?:achieved|obtained|earned|received)\s+(?:soc\s*2|iso\s*27001|pci\s*dss|hipaa|compliance)",
    r"(?:security\s+update|security\s+advisory|security\s+incident|data\s+breach|vulnerability\s+disclosure)",
    r"(?:bug\s+bounty|responsible\s+disclosure|security\s+researcher)",
    r"(?:penetration\s+test|security\s+audit)\s+(?:report|findings|results|summary)",
    r"(?:we|our)\s+(?:are|is)\s+(?:hiring|looking\s+for)\s+(?:a\s+)?(?:security\s+engineer|security\s+analyst|appsec|ciso|security\s+architect)",
    r"(?:our|we)\s+(?:security\s+team|infosec\s+team)\s+(?:has|have|is)",
    # Broader patterns for security activity
    r"(?:security|vulnerability|compliance)\s+(?:review|assessment|audit|testing)",
    r"(?:penetration|vulnerability|security)\s+(?:testing|assessment|audit)\s+(?:completed|done|finished)",
    r"(?:SOC\s*2|ISO\s*27001|HIPAA|PCI\s*DSS|GDPR)\s+(?:certification|compliance|audit|certified)",
]


class CompanyBlogCybersecurityCollector(BaseCybersecurityCollector):
    """Collects cybersecurity signals from company security/trust pages."""

    source_name = "company_blog"
    source_tier = 1  # Direct company announcements are high-value

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        company_urls: list[str] | None = None,
        max_items: int = 50,
        lookback_days: int = 90,
    ) -> None:
        super().__init__(http_client)
        self.company_urls = company_urls or []
        self.max_items = max_items
        self.lookback_days = lookback_days

    async def collect(self) -> Sequence[RawSignal]:
        """Collect cybersecurity signals from company blogs."""
        all_signals: list[RawSignal] = []

        for company_url in self.company_urls:
            try:
                signals = await self._check_company(company_url)
                all_signals.extend(signals)
                # Delay between companies to be polite
                await asyncio.sleep(1.0)
            except Exception as e:
                logger.warning("CompanyBlog collector failed for %s: %s", company_url, e)
                continue

        all_signals.sort(key=lambda s: s.score, reverse=True)
        logger.info("CompanyBlog collector found %d signals total", len(all_signals))
        return all_signals[: self.max_items]

    async def _check_company(self, company_url: str) -> list[RawSignal]:
        """Check a company's security/trust pages for signals."""
        signals = []
        base_url = company_url.rstrip("/")

        # Pages to check
        pages_to_check = [
            f"{base_url}/security",
            f"{base_url}/trust",
            f"{base_url}/compliance",
            f"{base_url}/privacy",
            f"{base_url}/status",
            f"{base_url}/blog",
            f"{base_url}/news",
            f"{base_url}/about",
        ]

        for page_url in pages_to_check:
            try:
                response = await self.http_client.get(
                    page_url,
                    timeout=10.0,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                )
                if response.status_code == 200:
                    page_signals = self._extract_signals_from_page(
                        response.text[:50000], page_url, company_url
                    )
                    signals.extend(page_signals)
                elif response.status_code == 403:
                    logger.debug("CompanyBlog: 403 for %s", page_url)
                elif response.status_code == 404:
                    logger.debug("CompanyBlog: 404 for %s", page_url)
                else:
                    logger.debug("CompanyBlog: %d for %s", response.status_code, page_url)
            except httpx.TimeoutException:
                logger.debug("CompanyBlog: timeout for %s", page_url)
            except httpx.RequestError as e:
                logger.debug("CompanyBlog: request error for %s: %s", page_url, e)
            except Exception as e:
                logger.debug("CompanyBlog: unexpected error for %s: %s", page_url, e)
                continue

        return signals

    def _extract_signals_from_page(
        self, html: str, page_url: str, company_url: str
    ) -> list[RawSignal]:
        """Extract security signals from a page."""
        signals = []

        # Check for security-related content
        html_lower = html.lower()

        for pattern in SECURITY_CONTENT_PATTERNS:
            matches = re.finditer(pattern, html_lower)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 200)
                end = min(len(html), match.end() + 200)
                context = html[start:end]
                # Clean HTML
                context = re.sub(r'<[^>]+>', ' ', context).strip()
                context = re.sub(r'\s+', ' ', context)[:500]

                score = self._calculate_signal_score(context)

                signals.append(RawSignal(
                    source="company_blog",
                    source_tier=self.source_tier,
                    url=page_url,
                    title=f"Security announcement from {company_url}",
                    content=context,
                    score=score,
                    metadata={
                        "company_url": company_url,
                        "page_url": page_url,
                        "pattern_matched": pattern[:50],
                    },
                ))

        # Check for links to security-related content
        link_pattern = re.compile(
            r'<a[^>]+href="([^"]*(?:security|compliance|audit|vulnerability|incident)[^"]*)"',
            re.IGNORECASE
        )
        for link_match in link_pattern.finditer(html):
            link_url = link_match.group(1)
            if not link_url.startswith("http"):
                link_url = f"{company_url.rstrip('/')}/{link_url.lstrip('/')}"

            signals.append(RawSignal(
                source="company_blog",
                source_tier=self.source_tier,
                url=link_url,
                title=f"Security page link from {company_url}",
                content=f"Found security-related link: {link_url}",
                score=5,
                metadata={
                    "company_url": company_url,
                    "link_url": link_url,
                },
            ))

        return signals

    def _calculate_signal_score(self, text: str) -> int:
        """Calculate signal strength score."""
        text_lower = text.lower()
        score = 0

        # High-value signals
        high_value = [
            "penetration test", "security audit", "vulnerability assessment",
            "soc 2", "iso 27001", "security incident", "data breach",
            "bug bounty", "responsible disclosure", "pci dss", "hipaa",
            "gdpr compliance", "security assessment",
        ]
        for kw in high_value:
            if kw in text_lower:
                score += 10

        # Medium signals
        medium_value = [
            "compliance", "security team", "security engineer",
            "security assessment", "security review", "security testing",
            "vulnerability", "audit", "certification",
        ]
        for kw in medium_value:
            if kw in text_lower:
                score += 5

        return score
