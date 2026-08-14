"""Social media collector for Indian ecommerce businesses."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from packages.ecommerce_leads.collectors.ecommerce_detector import USER_AGENTS
from packages.ecommerce_leads.models import RawEcommerceLead

logger = logging.getLogger(__name__)


class SocialCollector:
    """Collect social media presence for ecommerce leads."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def enrich_social_links(
        self, website: str
    ) -> dict[str, str]:
        """Extract social media links from a website."""
        social_links: dict[str, str] = {}

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._headers,
                follow_redirects=True,
            ) as client:
                resp = await client.get(website)
                if resp.status_code != 200:
                    return social_links

                body = resp.text
                social_links = self._extract_social_links(body)

        except Exception as e:
            logger.debug("Failed to enrich social links for %s: %s", website, e)

        return social_links

    def _extract_social_links(self, html: str) -> dict[str, str]:
        """Extract social media links from HTML."""
        links: dict[str, str] = {}

        patterns = {
            "instagram": [
                re.compile(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
                re.compile(r'https?://(?:www\.)?instagr\.am/([a-zA-Z0-9_.]+)', re.IGNORECASE),
            ],
            "facebook": [
                re.compile(r'https?://(?:www\.)?facebook\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
                re.compile(r'https?://(?:www\.)?fb\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
            ],
            "linkedin": [
                re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/([a-zA-Z0-9_-]+)', re.IGNORECASE),
            ],
            "twitter": [
                re.compile(r'https?://(?:www\.)?twitter\.com/([a-zA-Z0-9_]+)', re.IGNORECASE),
                re.compile(r'https?://(?:www\.)?x\.com/([a-zA-Z0-9_]+)', re.IGNORECASE),
            ],
            "youtube": [
                re.compile(r'https?://(?:www\.)?youtube\.com/(?:c/|channel/|@)([a-zA-Z0-9_-]+)', re.IGNORECASE),
            ],
            "pinterest": [
                re.compile(r'https?://(?:www\.)?pinterest\.(?:com|in)/([a-zA-Z0-9_]+)', re.IGNORECASE),
            ],
        }

        for platform, platform_patterns in patterns.items():
            for pattern in platform_patterns:
                match = pattern.search(html)
                if match:
                    full_url = match.group(0)
                    links[platform] = full_url
                    break

        return links

    async def collect_instagram_businesses(
        self, hashtags: list[str] | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Collect Instagram business profiles (public data only)."""
        if hashtags is None:
            hashtags = [
                "indiand2c",
                "indianbrand",
                "shopindian",
                "madeinindia",
                "indianfashion",
                "indianskincare",
                "indianbeauty",
                "indianbrand",
                "d2cindia",
                "indianstartup",
            ]

        results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(
            timeout=self.timeout, headers=self._headers
        ) as client:
            for tag in hashtags[:limit]:
                try:
                    url = f"https://www.instagram.com/explore/tags/{tag}/"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        profiles = self._extract_instagram_profiles(resp.text)
                        results.extend(profiles[:10])
                except Exception:
                    continue

        return results[:limit]

    def _extract_instagram_profiles(self, html: str) -> list[dict[str, Any]]:
        """Extract Instagram profile data from page HTML."""
        profiles: list[dict[str, Any]] = []
        username_pattern = re.compile(r'"username":"([a-zA-Z0-9_.]+)"')
        matches = username_pattern.findall(html)
        seen: set[str] = set()
        for username in matches:
            if username not in seen and len(username) > 2:
                seen.add(username)
                profiles.append({
                    "platform": "instagram",
                    "handle": username,
                    "url": f"https://www.instagram.com/{username}/",
                })
        return profiles

    async def enrich_website_contacts(self, website: str) -> dict[str, Any]:
        """Extract contact information from website."""
        contacts: dict[str, Any] = {
            "emails": [],
            "phones": [],
            "whatsapp": "",
            "address": "",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=self._headers, follow_redirects=True
            ) as client:
                contact_urls = [
                    f"{website}/contact",
                    f"{website}/contact-us",
                    f"{website}/contactus",
                    f"{website}/pages/contact-us",
                    f"{website}/pages/contact",
                ]

                for url in contact_urls:
                    try:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            body = resp.text
                            emails = re.findall(
                                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                                body,
                            )
                            phones = re.findall(
                                r'(?:\+91[\s-]?)?[6-9]\d{9}', body
                            )
                            whatsapp = re.findall(
                                r'wa\.me/(\d+)', body
                            ) or re.findall(
                                r'api\.whatsapp\.com/send\?phone=(\d+)', body
                            )

                            contacts["emails"].extend(
                                e for e in emails
                                if not e.endswith((".png", ".jpg", ".gif", ".svg"))
                            )
                            contacts["phones"].extend(phones)
                            if whatsapp:
                                contacts["whatsapp"] = whatsapp[0]

                            addr_match = re.search(
                                r'<address[^>]*>(.*?)</address>', body, re.DOTALL | re.IGNORECASE
                            )
                            if addr_match:
                                contacts["address"] = re.sub(
                                    r'<[^>]+>', ' ', addr_match.group(1)
                                ).strip()

                            if contacts["emails"] or contacts["phones"]:
                                break
                    except Exception:
                        continue

        except Exception:
            pass

        contacts["emails"] = list(set(contacts["emails"]))[:5]
        contacts["phones"] = list(set(contacts["phones"]))[:3]
        return contacts
