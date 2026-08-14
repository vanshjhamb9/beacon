"""Ecommerce platform detection from website HTML."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


@dataclass
class PlatformDetection:
    """Result of platform detection."""

    platform: str
    confidence: float
    indicators: list[str]


PLATFORM_SIGNATURES: dict[str, list[re.Pattern[str]]] = {
    "shopify": [
        re.compile(r"cdn\.shopify\.com", re.IGNORECASE),
        re.compile(r"Shopify\.theme", re.IGNORECASE),
        re.compile(r"shopify-section", re.IGNORECASE),
        re.compile(r"shopify-payment-button", re.IGNORECASE),
        re.compile(r"Shopify\.routes", re.IGNORECASE),
        re.compile(r"myshopify\.com", re.IGNORECASE),
        re.compile(r"shopify\.json", re.IGNORECASE),
        re.compile(r"Shopify\.shop", re.IGNORECASE),
        re.compile(r"shopify-cart", re.IGNORECASE),
        re.compile(r"cdn\.shopify\.com/s/files", re.IGNORECASE),
        re.compile(r"assets\.shopify\.com", re.IGNORECASE),
        re.compile(r" shopify ", re.IGNORECASE),
    ],
    "woocommerce": [
        re.compile(r"wp-content/plugins/woocommerce", re.IGNORECASE),
        re.compile(r"woocommerce\.min\.css", re.IGNORECASE),
        re.compile(r"wc-cart-fragments", re.IGNORECASE),
        re.compile(r"add_to_cart_url", re.IGNORECASE),
        re.compile(r"woocommerce-layout", re.IGNORECASE),
        re.compile(r"woocommerce\.js", re.IGNORECASE),
        re.compile(r"wc_add_to_cart_params", re.IGNORECASE),
        re.compile(r"wp-content/themes/.*woocommerce", re.IGNORECASE),
        re.compile(r"woocommerce-cart", re.IGNORECASE),
        re.compile(r"class=\"woocommerce", re.IGNORECASE),
        re.compile(r"woocommerce_add_to_cart", re.IGNORECASE),
        re.compile(r"wp-json/wc", re.IGNORECASE),
    ],
    "magento": [
        re.compile(r"magento", re.IGNORECASE),
        re.compile(r"skin/frontend/", re.IGNORECASE),
        re.compile(r"Mage\.Cookies", re.IGNORECASE),
        re.compile(r"requirejs/magento", re.IGNORECASE),
        re.compile(r"static/frontend/", re.IGNORECASE),
        re.compile(r"Magento_Theme", re.IGNORECASE),
    ],
    "bigcommerce": [
        re.compile(r"bigcommerce\.com", re.IGNORECASE),
        re.compile(r"bigcommerce-theme", re.IGNORECASE),
        re.compile(r"bc-sf-filter", re.IGNORECASE),
        re.compile(r"BigCommerce", re.IGNORECASE),
    ],
    "wix": [
        re.compile(r"wix\.com", re.IGNORECASE),
        re.compile(r"wixstatic\.com", re.IGNORECASE),
        re.compile(r"X-Wix", re.IGNORECASE),
        re.compile(r"wix\.com/.*\.html", re.IGNORECASE),
    ],
    "prestashop": [
        re.compile(r"prestashop", re.IGNORECASE),
        re.compile(r"themes/prestashop", re.IGNORECASE),
    ],
}

CHATBOT_SIGNATURES: list[re.Pattern[str]] = [
    re.compile(r"intercom", re.IGNORECASE),
    re.compile(r"crisp\.chat", re.IGNORECASE),
    re.compile(r"drift\.com", re.IGNORECASE),
    re.compile(r"tawk\.to", re.IGNORECASE),
    re.compile(r"zendesk.*chat", re.IGNORECASE),
    re.compile(r"livechatinc\.com", re.IGNORECASE),
    re.compile(r"tidio", re.IGNORECASE),
    re.compile(r"freshdesk.*chat", re.IGNORECASE),
    re.compile(r"freshworks.*chat", re.IGNORECASE),
    re.compile(r"helpscout", re.IGNORECASE),
    re.compile(r"olark\.com", re.IGNORECASE),
    re.compile(r"hubspot.*chat", re.IGNORECASE),
    re.compile(r"widget\.whacco", re.IGNORECASE),
    re.compile(r"chatbot.*widget", re.IGNORECASE),
    re.compile(r"zendesk.*widget", re.IGNORECASE),
    re.compile(r"crisp.*widget", re.IGNORECASE),
    re.compile(r"intercom.*widget", re.IGNORECASE),
    re.compile(r"drift.*widget", re.IGNORECASE),
    re.compile(r"livechat", re.IGNORECASE),
    re.compile(r"chat\.widget", re.IGNORECASE),
    re.compile(r"customerly", re.IGNORECASE),
    re.compile(r"tidio.*chat", re.IGNORECASE),
]

WHATSAPP_SIGNATURES: list[re.Pattern[str]] = [
    re.compile(r"wa\.me/", re.IGNORECASE),
    re.compile(r"api\.whatsapp\.com", re.IGNORECASE),
    re.compile(r"whatsapp.*send", re.IGNORECASE),
    re.compile(r"chat\.whatsapp\.com", re.IGNORECASE),
    re.compile(r"whatsapp.*button", re.IGNORECASE),
    re.compile(r"whatsapp.*widget", re.IGNORECASE),
    re.compile(r"whatsapp.*link", re.IGNORECASE),
]

CRM_SIGNATURES: list[re.Pattern[str]] = [
    re.compile(r"hubspot", re.IGNORECASE),
    re.compile(r"salesforce", re.IGNORECASE),
    re.compile(r"zoho.*crm", re.IGNORECASE),
    re.compile(r"freshsales", re.IGNORECASE),
    re.compile(r"pipedrive", re.IGNORECASE),
    re.compile(r"close\.com", re.IGNORECASE),
    re.compile(r"zoho.*salesiq", re.IGNORECASE),
]

ANALYTICS_SIGNATURES: list[re.Pattern[str]] = [
    re.compile(r"google-analytics\.com", re.IGNORECASE),
    re.compile(r"googletagmanager\.com", re.IGNORECASE),
    re.compile(r"gtag\(", re.IGNORECASE),
    re.compile(r"ga\(", re.IGNORECASE),
    re.compile(r"fbq\(", re.IGNORECASE),
    re.compile(r"facebook\.net/en_US/fbevents", re.IGNORECASE),
    re.compile(r"pixel\.js", re.IGNORECASE),
    re.compile(r"hotjar\.com", re.IGNORECASE),
    re.compile(r"clarity\.ms", re.IGNORECASE),
    re.compile(r"segment\.com/analytics", re.IGNORECASE),
]


class EcommerceDetector:
    """Detect ecommerce platform and technologies from website HTML."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def detect(self, url: str) -> dict[str, Any]:
        """Detect platform and technologies for a URL."""
        result: dict[str, Any] = {
            "platform": "unknown",
            "platform_confidence": 0.0,
            "shopify_detected": False,
            "woocommerce_detected": False,
            "magento_detected": False,
            "chatbot_detected": False,
            "whatsapp_detected": False,
            "crm_detected": False,
            "indicators": [],
        }

        body = await self._fetch_page(url)
        if not body:
            logger.warning("Failed to fetch page for detection: %s", url)
            return result

        platform_result = self._detect_platform(body)
        result["platform"] = platform_result.platform
        result["platform_confidence"] = platform_result.confidence
        result["indicators"] = platform_result.indicators

        result["shopify_detected"] = platform_result.platform == "shopify"
        result["woocommerce_detected"] = platform_result.platform == "woocommerce"
        result["magento_detected"] = platform_result.platform == "magento"

        result["chatbot_detected"] = self._detect_chatbot(body)
        result["whatsapp_detected"] = self._detect_whatsapp(body)
        result["crm_detected"] = self._detect_crm(body)

        logger.info(
            "Detection for %s: platform=%s (%.2f), chatbot=%s, whatsapp=%s, crm=%s",
            url, result["platform"], result["platform_confidence"],
            result["chatbot_detected"], result["whatsapp_detected"], result["crm_detected"],
        )

        return result

    async def _fetch_page(self, url: str) -> str:
        """Fetch page HTML with retry logic and multiple User-Agents."""
        for ua in USER_AGENTS:
            headers = {**self._headers, "User-Agent": ua}
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    headers=headers,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return resp.text
                    logger.debug("HTTP %d for %s with UA %s", resp.status_code, url, ua[:30])
            except httpx.TimeoutException:
                logger.debug("Timeout fetching %s", url)
                continue
            except httpx.ConnectError as e:
                logger.debug("Connect error for %s: %s", url, e)
                continue
            except Exception as e:
                logger.debug("Error fetching %s: %s", url, e)
                continue

        # Fallback: try without follow_redirects
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._headers,
                follow_redirects=False,
            ) as client:
                resp = await client.get(url)
                if resp.status_code in (301, 302, 307, 308):
                    location = resp.headers.get("location", "")
                    if location:
                        async with httpx.AsyncClient(
                            timeout=self.timeout,
                            headers=self._headers,
                            follow_redirects=True,
                        ) as client2:
                            resp2 = await client2.get(location)
                            if resp2.status_code == 200:
                                return resp2.text
        except Exception as e:
            logger.debug("Fallback redirect fetch failed for %s: %s", url, e)

        return ""

    def _detect_platform(self, html: str) -> PlatformDetection:
        scores: dict[str, tuple[float, list[str]]] = {}

        for platform, patterns in PLATFORM_SIGNATURES.items():
            matches = []
            for pattern in patterns:
                if pattern.search(html):
                    matches.append(pattern.pattern)
            if matches:
                confidence = min(1.0, len(matches) * 0.3)
                scores[platform] = (confidence, matches)

        if not scores:
            return PlatformDetection(platform="unknown", confidence=0.0, indicators=[])

        best = max(scores.items(), key=lambda x: x[1][0])
        return PlatformDetection(
            platform=best[0],
            confidence=best[1][0],
            indicators=best[1][1],
        )

    def _detect_chatbot(self, html: str) -> bool:
        return any(p.search(html) for p in CHATBOT_SIGNATURES)

    def _detect_whatsapp(self, html: str) -> bool:
        return any(p.search(html) for p in WHATSAPP_SIGNATURES)

    def _detect_crm(self, html: str) -> bool:
        return any(p.search(html) for p in CRM_SIGNATURES)
