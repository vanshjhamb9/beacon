"""Contact enrichment for ecommerce leads."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from packages.ecommerce_leads.collectors.ecommerce_detector import USER_AGENTS
from packages.ecommerce_leads.models import EnrichedEcommerceLead

logger = logging.getLogger(__name__)

FOUNDER_ROLE_PATTERNS = [
    re.compile(r"founder", re.IGNORECASE),
    re.compile(r"co-founder", re.IGNORECASE),
    re.compile(r"co founder", re.IGNORECASE),
    re.compile(r"ceo", re.IGNORECASE),
    re.compile(r"owner", re.IGNORECASE),
    re.compile(r"proprietor", re.IGNORECASE),
    re.compile(r"director", re.IGNORECASE),
    re.compile(r"managing director", re.IGNORECASE),
    re.compile(r"md\b", re.IGNORECASE),
    re.compile(r"founding team", re.IGNORECASE),
]

DECISION_MAKER_PATTERNS = [
    re.compile(r"marketing\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"ecommerce\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"digital\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"business\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"growth\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"product\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"operations?\s*(head|manager|director)", re.IGNORECASE),
    re.compile(r"sales?\s*(head|manager|director)", re.IGNORECASE),
]

EMAIL_BLACKLIST = {
    "example@example.com", "test@test.com", "email@example.com",
    "your@email.com", "name@domain.com", "user@example.com",
    "info@example.com", "support@example.com",
}

EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".webp", ".ico", ".woff", ".woff2", ".ttf"}


class ContactEnricher:
    """Enrich contact information for ecommerce leads."""

    def __init__(self, *, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def enrich(self, lead: EnrichedEcommerceLead) -> EnrichedEcommerceLead:
        """Enrich contact information from website."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=self._headers, follow_redirects=True
            ) as client:
                await self._find_emails(client, lead)
                await self._find_phones(client, lead)
                await self._find_whatsapp(client, lead)
                await self._find_decision_makers(client, lead)
        except Exception as e:
            logger.debug("Contact enrichment failed for %s: %s", lead.raw.website, e)

        return lead

    async def _find_emails(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Find email addresses from the website."""
        if lead.email:
            return

        pages_to_check = [
            lead.raw.website,
            f"{lead.raw.website}/contact",
            f"{lead.raw.website}/contact-us",
            f"{lead.raw.website}/pages/contact-us",
            f"{lead.raw.website}/pages/contact",
            f"{lead.raw.website}/about",
            f"{lead.raw.website}/about-us",
            f"{lead.raw.website}/pages/about-us",
            f"{lead.raw.website}/support",
            f"{lead.raw.website}/pages/support",
        ]

        emails_found: set[str] = set()
        for url in pages_to_check:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    body = resp.text
                    # Extract from HTML mailto links
                    mailto_emails = re.findall(
                        r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                        body,
                    )
                    emails_found.update(mailto_emails)

                    # Extract from text
                    text_emails = re.findall(
                        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                        body,
                    )
                    emails_found.update(text_emails)

                    if emails_found:
                        break
            except Exception:
                continue

        # Filter out bad emails
        filtered = []
        for e in emails_found:
            e_lower = e.lower()
            if any(e_lower.endswith(ext) for ext in EMAIL_EXTENSIONS):
                continue
            if e_lower in EMAIL_BLACKLIST:
                continue
            if len(e) > 100:
                continue
            filtered.append(e)

        if filtered:
            priority_emails = self._prioritize_emails(filtered)
            lead.email = priority_emails[0]
            lead.contact_source = "website"
            lead.contact_confidence = 0.7

    def _prioritize_emails(self, emails: list[str]) -> list[str]:
        """Prioritize emails by relevance."""
        priority_keywords = ["founder", "ceo", "owner", "hello", "info", "contact", "support"]
        scored: list[tuple[float, str]] = []
        for email in emails:
            score = 0.0
            local = email.split("@")[0].lower()
            for kw in priority_keywords:
                if kw in local:
                    score += 1.0
            if not any(c.isdigit() for c in local):
                score += 0.5
            scored.append((score, email))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored]

    async def _find_phones(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Find phone numbers from the website."""
        if lead.phone:
            return

        pages_to_check = [
            lead.raw.website,
            f"{lead.raw.website}/contact",
            f"{lead.raw.website}/contact-us",
            f"{lead.raw.website}/pages/contact-us",
            f"{lead.raw.website}/pages/contact",
            f"{lead.raw.website}/support",
        ]

        for url in pages_to_check:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    body = resp.text
                    # Extract from tel: links
                    tel_phones = re.findall(r'tel:([+]?[\d\s-]{10,15})', body)
                    if tel_phones:
                        phone = re.sub(r'[\s-]', '', tel_phones[0])
                        if len(phone) >= 10:
                            lead.phone = phone
                            if lead.contact_source:
                                lead.contact_confidence = max(lead.contact_confidence, 0.7)
                            else:
                                lead.contact_source = "website"
                                lead.contact_confidence = 0.7
                            return

                    # Indian phone patterns
                    phones = re.findall(
                        r'(?:\+91[\s-]?)?[6-9]\d{9}', body
                    )
                    # Also match with country code in various formats
                    phones += re.findall(
                        r'\+91[\s-]?\d{10}', body
                    )
                    # Match landline patterns
                    phones += re.findall(
                        r'0\d{2,4}[\s-]?\d{6,8}', body
                    )
                    
                    if phones:
                        phone = phones[0].replace(" ", "").replace("-", "")
                        lead.phone = phone
                        if lead.contact_source:
                            lead.contact_confidence = max(lead.contact_confidence, 0.6)
                        else:
                            lead.contact_source = "website"
                            lead.contact_confidence = 0.6
                        return
            except Exception:
                continue

    async def _find_whatsapp(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Find WhatsApp number from the website."""
        try:
            resp = await client.get(lead.raw.website)
            if resp.status_code == 200:
                body = resp.text
                wa_matches = re.findall(r'wa\.me/(\d+)', body)
                if not wa_matches:
                    wa_matches = re.findall(
                        r'api\.whatsapp\.com/send\?phone=(\d+)', body
                    )
                if wa_matches:
                    number = wa_matches[0]
                    if not lead.phone:
                        lead.phone = number
                    lead.whatsapp_detected = True
        except Exception:
            pass

    async def _find_decision_makers(
        self, client: httpx.AsyncClient, lead: EnrichedEcommerceLead
    ) -> None:
        """Try to find founder/decision maker from the website."""
        pages_to_check = [
            f"{lead.raw.website}/about",
            f"{lead.raw.website}/about-us",
            f"{lead.raw.website}/pages/about-us",
            f"{lead.raw.website}/our-story",
            f"{lead.raw.website}/team",
            f"{lead.raw.website}/pages/our-story",
            f"{lead.raw.website}/pages/team",
            f"{lead.raw.website}/company",
            f"{lead.raw.website}/pages/company",
        ]

        for url in pages_to_check:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    body = resp.text
                    name = self._extract_person_name(body)
                    if name:
                        lead.founder_name = name
                        # Detect role
                        for pattern in FOUNDER_ROLE_PATTERNS:
                            if pattern.search(body):
                                role_text = pattern.search(body).group(0)
                                lead.decision_maker_role = role_text.title()
                                break
                        if not lead.decision_maker_role:
                            for pattern in DECISION_MAKER_PATTERNS:
                                match = pattern.search(body)
                                if match:
                                    lead.decision_maker_role = match.group(0).strip().title()
                                    break
                        if not lead.decision_maker_role:
                            lead.decision_maker_role = "Founder"
                        return
            except Exception:
                continue

    def _extract_person_name(self, html: str) -> str:
        """Try to extract a person's name from about page HTML."""
        # Remove script and style tags
        clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
        
        name_patterns = [
            # "Founded by John Smith" or "Founded by: John Smith"
            re.compile(
                r'(?:founded by|founded by|started by|led by|CEO[:\s]+|Founder[:\s]+|Co-Founder[:\s]+)'
                r'\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})',
                re.IGNORECASE,
            ),
            # JSON-LD structured data
            re.compile(r'"name"\s*:\s*"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})"'),
            # Common Indian patterns: "Mr. Rahul Sharma" or "Ms. Priya Patel"
            re.compile(r'(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})'),
            # About page headings with names
            re.compile(r'<h[1-6][^>]*>.*?(?:founder|ceo|owner|director).*?</h[1-6]>', re.IGNORECASE | re.DOTALL),
            # Names after role titles in paragraphs
            re.compile(
                r'(?:founder|ceo|owner|director|managing director)\s+(?:and\s+)?(?:CEO\s+)?'
                r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})',
                re.IGNORECASE,
            ),
            # Meta author tags
            re.compile(r'<meta\s+name="author"\s+content="([^"]+)"', re.IGNORECASE),
            # Schema.org Person
            re.compile(r'"@type"\s*:\s*"Person"[^}]*"name"\s*:\s*"([^"]+)"'),
            re.compile(r'"name"\s*:\s*"([^"]+)"[^}]*"@type"\s*:\s*"Person"'),
        ]
        
        for pattern in name_patterns:
            match = pattern.search(clean)
            if match:
                name = match.group(1).strip() if match.lastindex else match.group(0).strip()
                # Clean HTML tags from name
                name = re.sub(r'<[^>]+>', '', name).strip()
                # Validate name: 2-4 words, each starting with capital, no numbers
                words = name.split()
                if 2 <= len(words) <= 4 and not any(c.isdigit() for c in name):
                    if all(w[0].isupper() for w in words if w):
                        return name
        return ""
