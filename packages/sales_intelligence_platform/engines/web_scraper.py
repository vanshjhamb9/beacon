"""Real web scraper for discovering contacts, technology, and business data from websites.

Stage 1-3: Business Discovery, Contact Discovery, Decision Maker Discovery.
No LLM. No fabrication. Only publicly available data with confidence scores.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# --- Regex Patterns ---

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

PHONE_REGEX = re.compile(
    r"(?:\+91[\s\-]?)?[6-9]\d{9}"
)

WHATSAPP_REGEX = re.compile(
    r"wa\.me/(\d{10,13})|api\.whatsapp\.com/send\?phone=(\d{10,13})"
)

TEL_REGEX = re.compile(
    r"tel:([+0-9\s\-()]+)"
)

MAILTO_REGEX = re.compile(
    r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"
)

LINKEDIN_REGEX = re.compile(
    r"linkedin\.com/(?:company|in)/([a-zA-Z0-9\-]+)"
)

INSTAGRAM_REGEX = re.compile(
    r"instagram\.com/([a-zA-Z0-9._]+)"
)

FACEBOOK_REGEX = re.compile(
    r"facebook\.com/([a-zA-Z0-9._]+)"
)

TWITTER_REGEX = re.compile(
    r"(?:twitter|x)\.com/([a-zA-Z0-9_]+)"
)

FOUNDER_PATTERNS = re.compile(
    r"(?:founder|co[\s-]?founder|ceo|owner|managing director|chief executive)[:\s]+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+){1,3})",
    re.IGNORECASE,
)

TITLE_PATTERNS = re.compile(
    r"(founder|co[\s-]?founder|ceo|cto|cmo|coo|cfo|head of|director|manager|vp|vice president|chief|owner|managing director)",
    re.IGNORECASE,
)

SCHEMA_ORG_REGEX = re.compile(
    r'"@type"\s*:\s*"Organization"', re.IGNORECASE
)

SCHEMA_EMAIL_REGEX = re.compile(
    r'"email"\s*:\s*"([^"]+)"'
)

SCHEMA_PHONE_REGEX = re.compile(
    r'"telephone"\s*:\s*"([^"]+)"'
)

SCHEMA_FOUNDER_REGEX = re.compile(
    r'"founder"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"'
)

SCHEMA_NAME_REGEX = re.compile(
    r'"name"\s*:\s*"([^"]+)"'
)

# Pages to crawl for contact info
CONTACT_PAGES = [
    "/", "/about", "/about-us", "/about-us/",
    "/team", "/our-team", "/leadership",
    "/contact", "/contact-us", "/contactus",
    "/support", "/help", "/faq",
    "/careers", "/jobs",
    "/privacy-policy", "/privacy",
    "/terms", "/terms-of-service",
    "/shipping", "/shipping-policy",
    "/returns", "/return-policy",
    "/pages/about-us", "/pages/contact-us",
    "/pages/shipping-policy", "/pages/return-policy",
]

# Technology detection signatures
SHOPIFY_SIGNATURES = [
    "cdn.shopify.com", "Shopify.theme", "shopify-section",
    "shopify-payment-button", "myshopify.com",
    "ShopifyAnalytics", "Shopify.",
]

WOOCOMMERCE_SIGNATURES = [
    "woocommerce", "wc-", "wp-content/plugins/woocommerce",
    "/cart/", "/checkout/",
]

MAGENTO_SIGNATURES = [
    "Mage.", "magento", "skin/frontend/",
    "static/frontend/", "Magento_",
]

BIGCOMMERCE_SIGNATURES = [
    "bigcommerce", "cdn11.bigcommerce.com",
    "bc-sell-widget",
]

# Support tool signatures
INTERCOM_SIGNATURES = ["intercom", "intercomSettings", "intercomid"]
ZENDESK_SIGNATURES = ["zendesk", "zdassets.com", "zd-static.com"]
FRESHDESK_SIGNATURES = ["freshdesk", "freshworks.com"]
TIDIO_SIGNATURES = ["tidio", "tidio-chat"]
GORGIAS_SIGNATURES = ["gorgias", "gorgiaschat"]
CRISP_SIGNATURES = ["crisp", "crisp.chat"]
LIVECHAT_SIGNATURES = ["livechat", "livechatinc.com"]
HUBSPOT_CHAT_SIGNATURES = ["hs-conversations", "hubspot", "hs-scripts"]
WHATSAPP_WIDGET_SIGNATURES = ["whatsapp-widget", "wa-widget", "whatsapp-chat"]

# Analytics signatures
GA_SIGNATURES = ["google-analytics.com", "googletagmanager.com", "gtag("]
META_PIXEL_SIGNATURES = ["facebook.net/en_US/fbevents", "fbq("]
CLARITY_SIGNATURES = ["clarity.ms"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class ScrapedContacts:
    """Contacts discovered from website scraping."""
    emails: list[dict[str, Any]] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    whatsapp_numbers: list[str] = field(default_factory=list)
    linkedin_urls: list[str] = field(default_factory=list)
    instagram_urls: list[str] = field(default_factory=list)
    facebook_urls: list[str] = field(default_factory=list)
    twitter_urls: list[str] = field(default_factory=list)
    decision_makers: list[dict[str, Any]] = field(default_factory=list)
    schema_org_data: dict[str, Any] = field(default_factory=dict)
    source_urls: list[str] = field(default_factory=list)


@dataclass
class ScrapedTechnology:
    """Technology stack discovered from website."""
    platform: str = ""
    shopify: bool = False
    woocommerce: bool = False
    magento: bool = False
    bigcommerce: bool = False
    support_tools: list[str] = field(default_factory=list)
    chatbot_detected: bool = False
    chatbot_tool: str = ""
    analytics: list[str] = field(default_factory=list)
    ai_tools: list[str] = field(default_factory=list)
    whatsapp_widget: bool = False
    live_chat: bool = False
    crm_detected: bool = False


@dataclass
class ScrapedBusiness:
    """Business data discovered from website."""
    company_name: str = ""
    description: str = ""
    category: str = ""
    city: str = ""
    state: str = ""
    country: str = "India"
    product_count: int = 0
    has_ecommerce: bool = False
    estimated_size: str = ""
    page_count: int = 0


@dataclass
class ScrapeResult:
    """Complete result from scraping a website."""
    domain: str
    business: ScrapedBusiness = field(default_factory=ScrapedBusiness)
    contacts: ScrapedContacts = field(default_factory=ScrapedContacts)
    technology: ScrapedTechnology = field(default_factory=ScrapedTechnology)
    scraped_at: str = ""
    errors: list[str] = field(default_factory=list)


class WebScraper:
    """Real website scraper for sales intelligence."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self._headers = HEADERS

    async def scrape(self, domain: str) -> ScrapeResult:
        """Scrape a website completely for all sales intelligence data."""
        result = ScrapeResult(domain=domain, scraped_at=datetime.now(UTC).isoformat())

        urls_to_try = self._build_url_list(domain)
        all_html = ""
        all_headers: dict[str, str] = {}

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,
            verify=False,
        ) as client:
            for url in urls_to_try:
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        all_html += "\n" + r.text[:80000]
                        result.contacts.source_urls.append(url)
                        if not all_headers:
                            all_headers = dict(r.headers)
                except Exception as e:
                    logger.debug("Failed to fetch %s: %s", url, e)
                    continue

                if len(all_html) > 300000:
                    break

        if not all_html:
            result.errors.append(f"Could not fetch any pages for {domain}")
            return result

        # Stage 1: Business Discovery
        result.business = self._extract_business_data(all_html, domain)

        # Stage 2: Contact Discovery
        result.contacts = self._extract_contacts(all_html, domain, result.contacts)

        # Stage 3: Decision Maker Discovery
        result.contacts.decision_makers = self._extract_decision_makers(all_html)

        # Stage 4: Technology Detection
        result.technology = self._detect_technology(all_html, all_headers)

        return result

    def _build_url_list(self, domain: str) -> list[str]:
        """Build list of URLs to crawl."""
        urls = []
        base = f"https://{domain}"
        www_base = f"https://www.{domain}"

        for url_base in [base, www_base]:
            for page in CONTACT_PAGES:
                urls.append(f"{url_base}{page}")

        return urls

    def _extract_business_data(self, html: str, domain: str) -> ScrapedBusiness:
        """Extract business information from HTML."""
        biz = ScrapedBusiness(domain=domain)

        # Extract title
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            biz.company_name = title_match.group(1).strip().split("|")[0].strip().split(" -")[0].strip()

        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', html, re.IGNORECASE)
        if desc_match:
            biz.description = desc_match.group(1).strip()

        # Detect e-commerce
        ecom_indicators = ["add to cart", "add to bag", "buy now", "shop now", "checkout", "product"]
        html_lower = html.lower()
        biz.has_ecommerce = any(ind in html_lower for ind in ecom_indicators)

        # Estimate product count from JSON-LD
        product_matches = re.findall(r'"@type"\s*:\s*"Product"', html)
        if product_matches:
            biz.product_count = len(product_matches)

        return biz

    def _extract_contacts(self, html: str, domain: str, contacts: ScrapedContacts) -> ScrapedContacts:
        """Extract all contact information from HTML."""
        # Emails
        raw_emails = EMAIL_REGEX.findall(html)
        mailto_emails = MAILTO_REGEX.findall(html)
        all_emails = list(set(raw_emails + mailto_emails))

        generic = {
            "noreply", "no-reply", "donotreply", "mailer-daemon",
            "postmaster", "hostmaster", "abuse", "webmaster",
            " wordpress@", "example@", "test@",
        }
        filtered_emails = []
        for e in all_emails:
            e_lower = e.lower()
            if not any(g in e_lower for g in generic):
                if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js", ".webp")):
                    email_type = self._classify_email(e)
                    filtered_emails.append({
                        "email": e,
                        "type": email_type,
                        "confidence": 0.9 if email_type == "business" else 0.7,
                        "source_url": domain,
                    })

        contacts.emails = filtered_emails[:10]

        # Phones
        raw_phones = PHONE_REGEX.findall(html)
        tel_phones = TEL_REGEX.findall(html)
        all_phones = list(set(raw_phones + tel_phones))

        formatted_phones = []
        for p in all_phones:
            p = p.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not p.startswith("+91") and len(p) == 10:
                p = "+91" + p
            elif not p.startswith("+91") and len(p) > 10:
                p = "+" + p
            if p not in formatted_phones:
                formatted_phones.append(p)

        contacts.phones = formatted_phones[:5]

        # WhatsApp
        wa_matches = WHATSAPP_REGEX.findall(html)
        for match in wa_matches:
            num = match[0] if match[0] else match[1]
            if num and num not in contacts.whatsapp_numbers:
                if not num.startswith("+91"):
                    num = "+91" + num
                contacts.whatsapp_numbers.append(num)

        # LinkedIn
        linkedin_matches = LINKEDIN_REGEX.findall(html)
        contacts.linkedin_urls = list(set(
            f"https://www.linkedin.com/company/{m}" for m in linkedin_matches
        ))[:5]

        # Social
        for match in INSTAGRAM_REGEX.findall(html):
            url = f"https://www.instagram.com/{match}"
            if url not in contacts.instagram_urls:
                contacts.instagram_urls.append(url)

        for match in FACEBOOK_REGEX.findall(html):
            url = f"https://www.facebook.com/{match}"
            if url not in contacts.facebook_urls:
                contacts.facebook_urls.append(url)

        for match in TWITTER_REGEX.findall(html):
            url = f"https://x.com/{match}"
            if url not in contacts.twitter_urls:
                contacts.twitter_urls.append(url)

        # Schema.org Organization data
        contacts.schema_org_data = self._extract_schema_org(html)

        return contacts

    def _classify_email(self, email: str) -> str:
        """Classify email type."""
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

    def _extract_decision_makers(self, html: str) -> list[dict[str, Any]]:
        """Extract decision maker names from HTML."""
        dms = []
        seen = set()

        # Founder/CEO patterns
        for match in FOUNDER_PATTERNS.finditer(html):
            name = match.group(1).strip()
            name_parts = name.split()
            if len(name_parts) >= 2 and len(name) < 50:
                name_key = name.lower()
                if name_key not in seen:
                    seen.add(name_key)
                    # Try to find the title nearby
                    start = max(0, match.start() - 100)
                    context = html[start:match.end() + 100]
                    title_match = TITLE_PATTERNS.search(context)
                    title = title_match.group(1) if title_match else "Founder"
                    dms.append({
                        "name": name,
                        "normalized_role": title.lower().strip(),
                        "confidence": 0.7,
                        "source_url": "website",
                    })

        return dms[:10]

    def _extract_schema_org(self, html: str) -> dict[str, Any]:
        """Extract Schema.org Organization data."""
        data: dict[str, Any] = {}

        if SCHEMA_ORG_REGEX.search(html):
            emails = SCHEMA_EMAIL_REGEX.findall(html)
            if emails:
                data["email"] = emails[0]

            phones = SCHEMA_PHONE_REGEX.findall(html)
            if phones:
                data["telephone"] = phones[0]

            founders = SCHEMA_FOUNDER_REGEX.findall(html)
            if founders:
                data["founder"] = founders[0]

            names = SCHEMA_NAME_REGEX.findall(html)
            if names:
                data["name"] = names[0]

        return data

    def _detect_technology(self, html: str, headers: dict[str, str]) -> ScrapedTechnology:
        """Detect technology stack from HTML and headers."""
        tech = ScrapedTechnology()
        html_lower = html.lower()
        header_str = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()

        # Platform detection
        all_text = html_lower + " " + header_str
        if any(s.lower() in all_text for s in SHOPIFY_SIGNATURES):
            tech.shopify = True
            tech.platform = "Shopify"
        elif any(s.lower() in all_text for s in WOOCOMMERCE_SIGNATURES):
            tech.woocommerce = True
            tech.platform = "WooCommerce"
        elif any(s.lower() in all_text for s in MAGENTO_SIGNATURES):
            tech.magento = True
            tech.platform = "Magento"
        elif any(s.lower() in all_text for s in BIGCOMMERCE_SIGNATURES):
            tech.bigcommerce = True
            tech.platform = "BigCommerce"
        else:
            tech.platform = "Custom"

        # Support tools
        support_map = {
            "Intercom": INTERCOM_SIGNATURES,
            "Zendesk": ZENDESK_SIGNATURES,
            "Freshdesk": FRESHDESK_SIGNATURES,
            "Tidio": TIDIO_SIGNATURES,
            "Gorgias": GORGIAS_SIGNATURES,
            "Crisp": CRISP_SIGNATURES,
            "LiveChat": LIVECHAT_SIGNATURES,
            "HubSpot Chat": HUBSPOT_CHAT_SIGNATURES,
        }
        for tool, sigs in support_map.items():
            if any(s.lower() in all_text for s in sigs):
                tech.support_tools.append(tool)

        tech.chatbot_detected = len(tech.support_tools) > 0
        if tech.support_tools:
            tech.chatbot_tool = tech.support_tools[0]

        # WhatsApp widget
        tech.whatsapp_widget = any(s.lower() in all_text for s in WHATSAPP_WIDGET_SIGNATURES)

        # Live chat
        tech.live_chat = any(t in tech.support_tools for t in ["Intercom", "Tidio", "Gorgias", "Crisp", "LiveChat"])

        # CRM
        tech.crm_detected = any(t in tech.support_tools for t in ["HubSpot Chat", "Zendesk", "Freshdesk"])

        # Analytics
        if any(s.lower() in all_text for s in GA_SIGNATURES):
            tech.analytics.append("Google Analytics")
        if any(s.lower() in all_text for s in META_PIXEL_SIGNATURES):
            tech.analytics.append("Meta Pixel")
        if any(s.lower() in all_text for s in CLARITY_SIGNATURES):
            tech.analytics.append("Microsoft Clarity")

        return tech
