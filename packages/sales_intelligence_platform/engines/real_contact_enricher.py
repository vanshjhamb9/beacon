"""Real contact enrichment - V2 with DuckDuckGo, concurrent requests, better filtering.

CTO-grade lead enrichment pipeline that finds:
- Real email addresses (support, sales, founder, general)
- Real phone numbers (Indian mobile + landline, filtered for business)
- Real decision maker names and roles (from JSON-LD, meta tags, page content)
- LinkedIn company pages
- Social media profiles
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}")
TEL_REGEX = re.compile(r"tel:([+0-9\s\-()]+)")
LINKEDIN_REGEX = re.compile(r"linkedin\.com/(?:company|in)/([a-zA-Z0-9\-]+)")
INSTAGRAM_REGEX = re.compile(r"instagram\.com/([a-zA-Z0-9._]+)")
FACEBOOK_REGEX = re.compile(r"facebook\.com/([a-zA-Z0-9._]+)")

GENERIC_EMAILS = {
    "noreply", "no-reply", "donotreply", "mailer-daemon",
    "postmaster", "hostmaster", "abuse", "webmaster",
    "wordpress@", "example@", "test@", "sentry@",
}

# Third-party domains that are NOT the company's own email
THIRD_PARTY_DOMAINS = {
    "sentry.io", "glood.ai", "stagheaddesigns.com", "shopify.com",
    "google.com", "facebook.com", "twitter.com", "instagram.com",
    "linkedin.com", "youtube.com", "googleapis.com", "cloudfront.net",
    "amazonaws.com", "bootstrapcdn.com", "jquery.com", "w3.org",
    "schema.org", "ogp.me", "apple.com", "microsoft.com",
}

# Phone numbers that are clearly NOT business phones (product prices, review patterns)
PHONE_BLACKLIST_PATTERNS = [
    r"^\d{10}$",  # Raw 10 digits without +91 often junk
    r"^91\d{10}$",  # 12 digit without +
]

# Pages to try for contact info - prioritized order
CONTACT_PAGES = [
    "/pages/contact-us", "/contact-us", "/contact",
    "/pages/about-us", "/about-us", "/about",
    "/team", "/our-team", "/about/team", "/people",
    "/founders", "/leadership", "/services",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


@dataclass
class EnrichedContact:
    kind: str
    value: str
    label: str = ""
    source_url: str = ""
    confidence: float = 0.5
    is_verified: bool = False


@dataclass
class DecisionMaker:
    name: str
    role: str
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    confidence: float = 0.5
    source_url: str = ""


@dataclass
class EnrichmentResult:
    company_name: str = ""
    domain: str = ""
    emails: list[EnrichedContact] = field(default_factory=list)
    phones: list[EnrichedContact] = field(default_factory=list)
    decision_makers: list[DecisionMaker] = field(default_factory=list)
    linkedin_urls: list[str] = field(default_factory=list)
    instagram_urls: list[str] = field(default_factory=list)
    facebook_urls: list[str] = field(default_factory=list)
    founder_name: str = ""
    founder_email: str = ""
    founder_phone: str = ""
    support_email: str = ""
    sales_email: str = ""
    general_email: str = ""
    business_phone: str = ""
    pages_scraped: int = 0
    errors: list[str] = field(default_factory=list)


class RealContactEnricher:
    """V2: Faster, more reliable contact enrichment."""

    def __init__(
        self,
        *,
        timeout: float = 8.0,
        delay: float = 1.0,
        max_concurrent: int = 2,
        allow_guesses: bool = False,
        max_pages: int = 15,
        light_search: bool = False,
    ):
        self.timeout = timeout
        self.delay = delay
        self.max_concurrent = max_concurrent
        self.allow_guesses = allow_guesses
        self.max_pages = max_pages
        self.light_search = light_search
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def enrich(
        self,
        domain: str,
        company_name: str = "",
        *,
        founder_name: str = "",
        allow_guesses: bool | None = None,
    ) -> EnrichmentResult:
        result = EnrichmentResult(
            domain=domain,
            company_name=company_name,
            founder_name=founder_name or "",
        )
        guesses = self.allow_guesses if allow_guesses is None else allow_guesses

        # Strategy 0: Check curated knowledge base first (instant, high confidence)
        try:
            from .curated_founders import enrich_with_curated_data
            await enrich_with_curated_data(domain, result)
        except ImportError:
            pass

        # Run homepage + contact/team pages + same-domain link follow
        await self._scrape_website_pages(domain, result)

        # Search engines (DuckDuckGo first, Bing; Google skipped — 429)
        await self._search_contacts(domain, company_name, result, founder_name=founder_name)

        # Optional pattern guesses (off by default — real data only)
        if guesses:
            self._guess_email_patterns(domain, result)

        # Classify and prioritize
        self._classify_contacts(result)

        return result

    def _get_headers(self) -> dict:
        import random
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> str:
        async with self._semaphore:
            try:
                r = await client.get(url, headers=self._get_headers(), follow_redirects=True)
                if r.status_code == 200:
                    return r.text[:200000]
            except Exception as e:
                logger.debug("Failed %s: %s", url, e)
        return ""

    async def _scrape_website_pages(self, domain: str, result: EnrichmentResult):
        """Fetch homepage + contact/team pages, then follow same-domain links up to max_pages."""
        from urllib.parse import urljoin, urlparse

        seed_urls: list[str] = []
        for base in [f"https://{domain}", f"https://www.{domain}"]:
            seed_urls.append(base)
            for path in CONTACT_PAGES:
                seed_urls.append(f"{base}{path}")

        seen: set[str] = set()
        queue: list[str] = []
        for url in seed_urls:
            key = url.split("#")[0].rstrip("/").lower()
            if key not in seen:
                seen.add(key)
                queue.append(url)

        href_re = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        domain_root = domain.lower().removeprefix("www.")

        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            idx = 0
            while idx < len(queue) and result.pages_scraped < self.max_pages:
                batch = queue[idx : idx + self.max_concurrent]
                idx += len(batch)
                pages = await asyncio.gather(*[self._fetch(client, url) for url in batch])
                for url, page in zip(batch, pages):
                    if not isinstance(page, str) or not page or len(page) < 300:
                        continue
                    self._extract_all_contacts(page, url, result)
                    result.pages_scraped += 1
                    if result.pages_scraped >= self.max_pages:
                        break
                    # Discover same-domain links for deeper crawl
                    for href in href_re.findall(page):
                        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                            continue
                        absolute = urljoin(url, href)
                        parsed = urlparse(absolute)
                        host = (parsed.hostname or "").lower().removeprefix("www.")
                        if host != domain_root:
                            continue
                        if parsed.scheme not in ("http", "https"):
                            continue
                        path = (parsed.path or "").lower()
                        if any(
                            path.endswith(ext)
                            for ext in (
                                ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp",
                                ".css", ".js", ".svg", ".zip", ".woff", ".woff2",
                                ".ttf", ".eot", ".ico", ".map", ".xml",
                            )
                        ):
                            continue
                        if "/_next/" in path or "/static/" in path or "/wp-json" in path:
                            continue
                        if "feed=" in absolute.lower() or "xmlrpc" in path:
                            continue
                        key = absolute.split("#")[0].rstrip("/").lower()
                        if key not in seen and len(queue) < self.max_pages * 3:
                            seen.add(key)
                            queue.append(absolute)

    async def _search_contacts(
        self,
        domain: str,
        company_name: str,
        result: EnrichmentResult,
        *,
        founder_name: str = "",
    ):
        """Search DuckDuckGo + Bing for contact data (Google skipped — 429)."""
        queries = [
            f'"{company_name}" founder CEO',
            f'"{company_name}" phone number',
        ]
        if founder_name:
            queries.insert(0, f'"{founder_name}" "{company_name}" email')
            queries.insert(1, f'"{founder_name}" "{company_name}" contact')
        if self.light_search:
            queries = queries[:2]

        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            for query in queries:
                if not self.light_search:
                    html = await self._search_duckduckgo(client, query)
                    if html:
                        self._extract_all_contacts(html, f"ddg:{query}", result)

                html = await self._search_bing(client, query)
                if html:
                    self._extract_all_contacts(html, f"bing:{query}", result)

                await asyncio.sleep(self.delay)

    async def _search_duckduckgo(self, client: httpx.AsyncClient, query: str) -> str:
        """Search via DuckDuckGo HTML version."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            r = await client.get(url, headers=self._get_headers(), follow_redirects=True)
            if r.status_code == 200:
                return r.text[:100000]
        except Exception as e:
            logger.debug("DDG failed: %s", e)
        return ""

    async def _search_google(self, client: httpx.AsyncClient, query: str) -> str:
        """Search via Google (may get rate-limited)."""
        try:
            url = f"https://www.google.com/search?q={quote_plus(query)}&num=5"
            r = await client.get(url, headers=self._get_headers(), follow_redirects=True)
            if r.status_code == 200:
                return r.text[:100000]
        except Exception as e:
            logger.debug("Google failed: %s", e)
        return ""

    async def _search_bing(self, client: httpx.AsyncClient, query: str) -> str:
        """Search via Bing."""
        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}&count=5"
            r = await client.get(url, headers=self._get_headers(), follow_redirects=True)
            if r.status_code == 200:
                return r.text[:100000]
        except Exception as e:
            logger.debug("Bing failed: %s", e)
        return ""

    def _extract_all_contacts(self, html: str, source_url: str, result: EnrichmentResult):
        """Extract all contact data from HTML."""
        # Determine company domain from source_url
        company_domain = ""
        if source_url and "://" in source_url:
            from urllib.parse import urlparse
            try:
                parsed = urlparse(source_url)
                host = parsed.hostname or ""
                if host.startswith("www."):
                    host = host[4:]
                company_domain = host
            except Exception:
                pass

        # Extract emails
        raw_emails = EMAIL_REGEX.findall(html)
        for email in raw_emails:
            email_lower = email.lower()
            if any(g in email_lower for g in GENERIC_EMAILS):
                continue
            if email.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js", ".webp", ".ico")):
                continue
            if len(email) > 80:
                continue

            # Filter out third-party domain emails
            email_domain = email.split("@")[1].lower()
            if email_domain in THIRD_PARTY_DOMAINS:
                continue
            # Skip if email domain doesn't match company domain and isn't a known business pattern
            if company_domain and email_domain != company_domain:
                # Allow if it looks like the company's own email (same root domain)
                company_root = company_domain.split(".")[-2] if "." in company_domain else ""
                email_root = email_domain.split(".")[-2] if "." in email_domain else ""
                if company_root and email_root and company_root != email_root:
                    continue

            if not any(e.value == email for e in result.emails):
                label = self._classify_email(email)
                result.emails.append(EnrichedContact(
                    kind="email", value=email, label=label,
                    source_url=source_url, confidence=0.9,
                ))

        # Extract phones - with quality filtering
        raw_phones = PHONE_REGEX.findall(html)
        tel_phones = TEL_REGEX.findall(html)

        for phone in raw_phones + tel_phones:
            phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not phone.startswith("+91") and len(phone) == 10:
                phone = "+91" + phone
            elif not phone.startswith("+91") and len(phone) > 10:
                phone = "+" + phone

            # Validate: must be +91 + 10 digits = 13 chars
            if len(phone) < 13 or len(phone) > 15:
                continue
            if not phone.startswith("+91"):
                continue
            # Must start with 6-9 after +91
            if len(phone) == 13 and phone[3] not in "6789":
                continue
            # Skip duplicates
            if any(p.value == phone for p in result.phones):
                continue

            # Context-based confidence: from tel: links = higher confidence
            confidence = 0.7
            if phone in tel_phones:
                confidence = 0.9  # Explicit tel: link = very likely business phone

            result.phones.append(EnrichedContact(
                kind="phone", value=phone, label="business",
                source_url=source_url, confidence=confidence,
            ))

        # Extract LinkedIn (preserve /in vs /company from source HTML)
        for kind, slug in re.findall(
            r"linkedin\.com/(company|in)/([a-zA-Z0-9\-]+)", html, re.IGNORECASE
        ):
            url = f"https://www.linkedin.com/{kind.lower()}/{slug}"
            if url not in result.linkedin_urls:
                result.linkedin_urls.append(url)

        # Extract social
        for match in INSTAGRAM_REGEX.findall(html):
            url = f"https://www.instagram.com/{match}"
            if url not in result.instagram_urls:
                result.instagram_urls.append(url)

        for match in FACEBOOK_REGEX.findall(html):
            url = f"https://www.facebook.com/{match}"
            if url not in result.facebook_urls:
                result.facebook_urls.append(url)

        # Extract founder/CEO from structured data and content
        self._extract_founder_names(html, source_url, result)

    def _extract_founder_names(self, html: str, source_url: str, result: EnrichmentResult):
        """Try multiple strategies to find founder/CEO names."""
        junk = {
            "new window", "return false", "instanceof", "var timeout",
            "navigator", "function", "typeof", "undefined", "null",
            "true", "false", "this.", "self.", "click here", "read more",
            "learn more", "shop now", "buy now", "add to",
            "loading", "search", "menu", "close", "open",
            "cookie", "privacy", "terms", "shipping",
        }

        # Strategy 1: JSON-LD structured data (highest confidence)
        json_ld_patterns = [
            r'"founder"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"',
            r'"founder"\s*:\s*"([^"]+)"',
            r'"name"\s*:\s*"([^"]+)"\s*,\s*"jobTitle"\s*:\s*"(?:Founder|CEO|Co-Founder|Chief Executive)"',
            r'"jobTitle"\s*:\s*"(?:Founder|CEO|Co-Founder)"\s*,\s*"name"\s*:\s*"([^"]+)"',
        ]
        for pattern in json_ld_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for name in matches:
                if self._is_valid_name(name, junk):
                    result.decision_makers.append(DecisionMaker(
                        name=name.strip(), role="Founder/CEO",
                        confidence=0.95, source_url=source_url,
                    ))

        # Strategy 2: Meta tags (high confidence)
        meta_patterns = [
            r'<meta[^>]*(?:author|creator)[^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*(?:author|creator)',
        ]
        for pattern in meta_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for name in matches:
                name = name.strip()
                if self._is_valid_name(name, junk):
                    result.decision_makers.append(DecisionMaker(
                        name=name, role="Author",
                        confidence=0.8, source_url=source_url,
                    ))

        # Strategy 3: HTML heading/paragraph patterns (high confidence)
        html_patterns = [
            r'<(?:h[1-6]|p|span|div|strong|b|td)[^>]*>\s*(?:Founder|CEO|Co-Founder|Chief Executive|Managing Director)\s*[:\-–—]?\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*<',
            r'(?:founded by|created by|started by|led by)\s+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'(?:Founder|CEO|Co-Founder)\s*[:\-–—]\s*([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        for pattern in html_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for name in matches:
                if self._is_valid_name(name, junk):
                    result.decision_makers.append(DecisionMaker(
                        name=name.strip(), role="Founder/CEO",
                        confidence=0.85, source_url=source_url,
                    ))

        # Strategy 4: Text content patterns (medium confidence)
        text_patterns = [
            r'(?:Founder|CEO|Co-Founder|Chief Executive|Managing Director)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[,]\s*(?:Founder|CEO|Co-Founder)',
        ]
        for pattern in text_patterns:
            matches = re.findall(pattern, html)
            for name in matches:
                if self._is_valid_name(name, junk):
                    result.decision_makers.append(DecisionMaker(
                        name=name.strip(), role="Founder",
                        confidence=0.7, source_url=source_url,
                    ))

    def _is_valid_name(self, name: str, junk: set) -> bool:
        """Validate that a string looks like a real person name."""
        name = name.strip()
        words = name.split()
        if not (2 <= len(words) <= 4):
            return False
        if not all(w.isalpha() and w[0].isupper() for w in words):
            return False
        if len(name) < 5 or len(name) > 50:
            return False
        if name.lower() in junk:
            return False
        return True

    def _classify_email(self, email: str) -> str:
        local = email.split("@")[0].lower()
        if any(p in local for p in ["founder", "ceo", "owner"]):
            return "founder"
        if any(p in local for p in ["support", "help", "care"]):
            return "support"
        if any(p in local for p in ["sales", "business", "partnerships"]):
            return "sales"
        if any(p in local for p in ["info", "hello", "hi", "contact"]):
            return "general"
        if any(p in local for p in ["marketing", "pr", "press"]):
            return "marketing"
        if any(p in local for p in ["hr", "jobs", "careers", "recruit"]):
            return "hr"
        return "business"

    def _guess_email_patterns(self, domain: str, result: EnrichmentResult):
        """If we found one email, guess common patterns."""
        if not result.emails:
            return
        email_domain = result.emails[0].value.split("@")[1]
        common_prefixes = ["info", "support", "sales", "hello", "contact", "help", "admin"]
        for prefix in common_prefixes:
            guessed = f"{prefix}@{email_domain}"
            if not any(e.value == guessed for e in result.emails):
                result.emails.append(EnrichedContact(
                    kind="email", value=guessed,
                    label=self._classify_email(guessed),
                    source_url="pattern_guess", confidence=0.35,
                ))

    def _classify_contacts(self, result: EnrichmentResult):
        """Classify and prioritize contacts."""
        for email in result.emails:
            if email.label == "founder" and not result.founder_email:
                result.founder_email = email.value
            elif email.label == "support" and not result.support_email:
                result.support_email = email.value
            elif email.label == "sales" and not result.sales_email:
                result.sales_email = email.value
            elif email.label == "general" and not result.general_email:
                result.general_email = email.value

        # Sort phones by confidence (tel: links first, then others)
        result.phones.sort(key=lambda p: p.confidence, reverse=True)
        for phone in result.phones:
            if not result.business_phone:
                result.business_phone = phone.value

        for dm in result.decision_makers:
            if not result.founder_name:
                result.founder_name = dm.name
