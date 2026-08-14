"""Enrichment pipeline with evidence collection.

Every detection has a state:
- VERIFIED_PRESENT: we found evidence it exists
- VERIFIED_ABSENT: we checked and it's not there
- UNKNOWN: we couldn't check

Every contact is validated:
- RFC email validation
- Reject JS/image/bundle filenames
- Never invent contacts

Every pain point has:
- evidence
- confidence
- source
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

from packages.ecommerce_leads.models import (
    DetectionState,
    EnrichedEcommerceLead,
    RawEcommerceLead,
    is_valid_email,
)

logger = logging.getLogger(__name__)


# ============================================================
# ENRICHMENT PATTERNS
# ============================================================

CHATBOT_SIGNATURES = [
    "intercom", "drift", "crisp", "tawk", "tidio",
    "zendesk chat", "freshchat", "livechat", "chatbot",
    "hubspot chat", "tawk.to", "crisp.chat",
]

WHATSAPP_SIGNATURES = ["wa.me", "whatsapp", "api.whatsapp", "whatsapp.com/send"]

CRM_SIGNATURES = ["salesforce", "hubspot", "zoho", "freshsales", "pipedrive"]

FOUNDER_PATTERNS = [
    r'"founder"\s*:\s*"([^"]+)"',
    r'"ceo"\s*:\s*"([^"]+)"',
    r'"cofounder"\s*:\s*"([^"]+)"',
    r'"co-founder"\s*:\s*"([^"]+)"',
    r'founded by ([A-Z][a-z]+ [A-Z][a-z]+)',
    r'Founder[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
    r'CEO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
]

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

PHONE_PATTERNS = [
    re.compile(r'\+91[\s-]?\d{10}'),
    re.compile(r'91[\s-]?\d{10}'),
]

SOCIAL_PATTERNS = {
    "instagram": re.compile(r'https?://(?:www\.)?instagram\.com/[^\s"\'<>]+'),
    "facebook": re.compile(r'https?://(?:www\.)?facebook\.com/[^\s"\'<>]+'),
    "twitter": re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[^\s"\'<>]+'),
    "linkedin": re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[^\s"\'<>]+'),
    "youtube": re.compile(r'https?://(?:www\.)?youtube\.com/(?:c/|channel/|@)[^\s"\'<>]+'),
}

PAIN_EVIDENCE_PATTERNS = {
    "faq_volume": re.compile(r'faq|frequently asked|help center|support center', re.IGNORECASE),
    "return_policy": re.compile(r'return|refund|exchange|replacement', re.IGNORECASE),
    "shipping_info": re.compile(r'shipping|delivery|dispatch|track(?:ing)?', re.IGNORECASE),
    "cod_available": re.compile(r'cash on delivery|cod|pay on delivery', re.IGNORECASE),
    "contact_page": re.compile(r'contact us|reach us|get in touch', re.IGNORECASE),
    "large_catalog": re.compile(r'(\d{2,})\s*(?:products?|items?|variants?)', re.IGNORECASE),
}


async def enrich_lead(
    client: httpx.AsyncClient,
    lead: RawEcommerceLead,
) -> EnrichedEcommerceLead:
    """Enrich a single lead with evidence-backed detection."""
    enriched = EnrichedEcommerceLead(raw=lead)

    try:
        resp = await client.get(lead.website, follow_redirects=True, timeout=15.0)
        if resp.status_code != 200:
            return enriched

        body = resp.text
        body_lower = body.lower()

        # === PLATFORM DETECTION ===
        if "shopify" in body_lower or "cdn.shopify.com" in body_lower:
            enriched.platform = "shopify"
            enriched.platform_source = "homepage_html"
        elif "woocommerce" in body_lower or "wp-content" in body_lower:
            enriched.platform = "woocommerce"
            enriched.platform_source = "homepage_html"

        # === CHATBOT DETECTION (three-state) ===
        chatbot_found = [s for s in CHATBOT_SIGNATURES if s in body_lower]
        if chatbot_found:
            enriched.chatbot_state = DetectionState.VERIFIED_PRESENT
            enriched.chatbot_evidence = f"Detected: {', '.join(chatbot_found[:3])}"
            enriched.chatbot_source = "homepage_html"
        else:
            # We checked — not found
            enriched.chatbot_state = DetectionState.VERIFIED_ABSENT
            enriched.chatbot_evidence = "Checked homepage HTML — no chatbot signatures found"
            enriched.chatbot_source = "homepage_html"

        # === WHATSAPP DETECTION (three-state) ===
        whatsapp_found = [s for s in WHATSAPP_SIGNATURES if s in body_lower]
        if whatsapp_found:
            enriched.whatsapp_state = DetectionState.VERIFIED_PRESENT
            enriched.whatsapp_evidence = f"Detected: {', '.join(whatsapp_found[:3])}"
            enriched.whatsapp_source = "homepage_html"
        else:
            enriched.whatsapp_state = DetectionState.VERIFIED_ABSENT
            enriched.whatsapp_evidence = "Checked homepage HTML — no WhatsApp signatures found"
            enriched.whatsapp_source = "homepage_html"

        # === CRM DETECTION (three-state) ===
        crm_found = [s for s in CRM_SIGNATURES if s in body_lower]
        if crm_found:
            enriched.crm_state = DetectionState.VERIFIED_PRESENT
            enriched.crm_evidence = f"Detected: {', '.join(crm_found[:3])}"
            enriched.crm_source = "homepage_html"
        else:
            enriched.crm_state = DetectionState.VERIFIED_ABSENT
            enriched.crm_evidence = "Checked homepage HTML — no CRM signatures found"
            enriched.crm_source = "homepage_html"

        # === FOUNDER DISCOVERY (P0) ===
        _extract_founder(enriched, body)

        # === CONTACT EXTRACTION (with validation) ===
        _extract_contacts(enriched, body, source="homepage_html")
        if not enriched.email:
            await _extract_contact_page_emails(client, lead, enriched)

        # === SOCIAL LINKS ===
        _extract_social_links(enriched, body)

        # === PRODUCT COUNT (evidence-based) ===
        _extract_product_count(enriched, body)

        # === PAIN POINT EVIDENCE ===
        _extract_pain_evidence(enriched, body)

        # === DESCRIPTION ===
        desc_match = re.search(
            r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
            body, re.IGNORECASE
        )
        if desc_match:
            lead.description = desc_match.group(1)[:500]

        # === EMPLOYEE COUNT (from About page) ===
        await _extract_about_page_info(client, lead, enriched)

    except Exception as e:
        logger.debug("Enrichment failed for %s: %s", lead.website, e)

    # Validate email
    if enriched.email:
        enriched.email_valid = is_valid_email(enriched.email)

    return enriched


def _extract_founder(enriched: EnrichedEcommerceLead, html: str) -> None:
    """Extract founder/CEO/owner from HTML."""
    # Words that look like names but aren't
    NOT_NAMES = {
        "man", "woman", "perfume", "product", "team", "brand", "shop",
        "buy", "sell", "cart", "order", "view", "read", "learn",
        "free", "best", "new", "top", "all", "our", "the",
    }
    for pattern in FOUNDER_PATTERNS:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            words = name.split()
            # Validate it looks like a real name (2-3 words, capitalized)
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                # Reject if any word is a common non-name
                if any(w.lower() in NOT_NAMES for w in words):
                    continue
                enriched.founder_name = name
                enriched.founder_source = "homepage_html"
                enriched.founder_confidence = 0.7

                # Determine role from pattern
                pattern_lower = pattern.lower()
                if "founder" in pattern_lower:
                    enriched.founder_role = "Founder"
                elif "ceo" in pattern_lower:
                    enriched.founder_role = "CEO"
                elif "co-founder" in pattern_lower or "cofounder" in pattern_lower:
                    enriched.founder_role = "Co-Founder"
                break


def _email_priority(email: str, brand_domain: str = "") -> int:
    """Lower is better. Prefer brand-domain hello/care/founder over CDN junk."""
    e = email.lower().strip()
    local = e.split("@", 1)[0]
    host = e.split("@", 1)[-1].replace("www.", "")
    brand = (brand_domain or "").lower().replace("www.", "").split("/")[0]
    junk_hosts = (
        "sentry.io",
        "example.com",
        "wixpress.com",
        "cloudflare",
        "schema.org",
        "github.com",
        "google.com",
        "facebook.com",
        "shopify.com",
        "myshopify.com",
    )
    if any(j in host for j in junk_hosts):
        return 1000
    if local in ("noreply", "no-reply", "donotreply", "mailer-daemon"):
        return 900
    # Franchise / PR / community inboxes are weak for founder COMAI pitch
    if local in ("franchise", "franchising", "community", "press", "media", "pr", "news", "investors", "ir"):
        return 750
    freemail = host in ("gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com")
    score = 50
    if brand:
        brand_match = host == brand or host.endswith("." + brand) or brand.endswith("." + host)
        # also allow brand root in host (e.g. mail.brand.com)
        root = brand.split(".", 1)[0]
        if not brand_match and root and len(root) >= 4 and root in host.split(".")[0]:
            brand_match = True
        if brand_match:
            score -= 40
        elif not freemail:
            score += 350  # off-domain corporate mailbox (e.g. Caprese→vipbags)
    preferred_locals = (
        "founder",
        "ceo",
        "hello",
        "hi",
        "care",
        "wecare",
        "contact",
        "info",
        "support",
        "team",
        "sales",
        "growth",
        "partners",
    )
    if local in preferred_locals or any(local.startswith(p) for p in preferred_locals):
        score -= 20
    if freemail:
        score -= 10  # personal inboxes often founders
    return score


def _extract_contacts(
    enriched: EnrichedEcommerceLead,
    html: str,
    *,
    source: str = "homepage_html",
) -> None:
    """Extract and validate contact information."""
    brand_domain = ""
    if enriched.raw and enriched.raw.domain:
        brand_domain = enriched.raw.domain.lower().replace("www.", "")
    elif enriched.raw and enriched.raw.website:
        brand_domain = re.sub(r"^https?://(www\.)?", "", enriched.raw.website.lower()).split("/")[0]

    emails = EMAIL_PATTERN.findall(html)
    business_emails = []
    for e in emails:
        if is_valid_email(e):
            business_emails.append(e.lower())
    business_emails = sorted(set(business_emails), key=lambda x: _email_priority(x, brand_domain))

    if business_emails and not enriched.email:
        enriched.email = business_emails[0]
        enriched.email_source = source
        enriched.email_valid = True
        # Promote personal-looking or founderish to founder_email
        top = business_emails[0]
        local = top.split("@", 1)[0]
        if local not in ("support", "care", "info", "hello", "contact", "customercare", "help") or top.endswith(
            ("@gmail.com", "@googlemail.com")
        ):
            if not enriched.founder_email:
                enriched.founder_email = top

    # Extract phones
    if not enriched.phone:
        for pattern in PHONE_PATTERNS:
            phones = pattern.findall(html)
            if phones:
                enriched.phone = phones[0]
                enriched.phone_source = source
                break


async def _extract_contact_page_emails(
    client: httpx.AsyncClient,
    lead: RawEcommerceLead,
    enriched: EnrichedEcommerceLead,
) -> None:
    """Follow common contact URLs when homepage has no usable email."""
    base = (lead.website or "").rstrip("/")
    if not base:
        return
    contact_urls = [
        f"{base}/pages/contact",
        f"{base}/pages/contact-us",
        f"{base}/contact",
    ]
    for url in contact_urls:
        try:
            resp = await client.get(url, follow_redirects=True, timeout=10.0)
            if resp.status_code != 200:
                continue
            _extract_contacts(enriched, resp.text, source="contact_page")
            if enriched.email:
                return
        except Exception:  # noqa: BLE001
            continue


def _extract_social_links(enriched: EnrichedEcommerceLead, html: str) -> None:
    """Extract social media links."""
    for platform, pattern in SOCIAL_PATTERNS.items():
        match = pattern.search(html)
        if match:
            enriched.social_links[platform] = match.group(0)


def _extract_product_count(enriched: EnrichedEcommerceLead, html: str) -> None:
    """Extract product count with evidence."""
    # Look for structured data
    patterns = [
        (r'"product_count"\s*:\s*(\d+)', "json_ld"),
        (r'"numberOfItems"\s*:\s*(\d+)', "json_ld"),
        (r'(\d+)\s+products?', "html_text"),
        (r'(\d+)\s+items?', "html_text"),
    ]

    for pattern, source in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            try:
                count = int(match.group(1))
                if count > 1:  # Never use 0 or 1
                    enriched.product_count = count
                    enriched.product_count_source = source
                    break
            except ValueError:
                continue

    # If no evidence, leave as None (unknown)


def _extract_pain_evidence(enriched: EnrichedEcommerceLead, html: str) -> None:
    """Extract pain point evidence with confidence."""
    pain_evidence = []

    for pain_type, pattern in PAIN_EVIDENCE_PATTERNS.items():
        matches = pattern.findall(html)
        if matches:
            if pain_type == "large_catalog":
                # Extract actual count
                count_match = re.search(r'(\d{2,})\s*(?:products?|items?|variants?)', html, re.IGNORECASE)
                if count_match:
                    count = int(count_match.group(1))
                    pain_evidence.append({
                        "type": pain_type,
                        "evidence": f"Catalog contains {count}+ products",
                        "confidence": 0.8,
                        "source": "homepage_html",
                    })
            else:
                pain_evidence.append({
                    "type": pain_type,
                    "evidence": f"Found {len(matches)} instances of {pain_type} references",
                    "confidence": min(0.9, 0.5 + len(matches) * 0.1),
                    "source": "homepage_html",
                })

    enriched.pain_points = pain_evidence


async def _extract_about_page_info(
    client: httpx.AsyncClient,
    lead: RawEcommerceLead,
    enriched: EnrichedEcommerceLead,
) -> None:
    """Try to extract info from About page."""
    about_urls = [
        lead.website.rstrip("/") + "/pages/about-us",
        lead.website.rstrip("/") + "/pages/about",
        lead.website.rstrip("/") + "/about",
        lead.website.rstrip("/") + "/pages/our-story",
    ]

    for about_url in about_urls:
        try:
            resp = await client.get(about_url, follow_redirects=True, timeout=10.0)
            if resp.status_code == 200:
                about_body = resp.text

                # Try founder patterns on about page
                if not enriched.founder_name:
                    _extract_founder(enriched, about_body)

                # Look for team size / employee count evidence
                size_patterns = [
                    (r'team of (\d+)', "about_page"),
                    (r'(\d+)\s+team members', "about_page"),
                    (r'(\d+)\s+employees', "about_page"),
                    (r'(\d+)\s+people', "about_page"),
                    (r'with (\d+) people', "about_page"),
                ]

                for pattern, source in size_patterns:
                    match = re.search(pattern, about_body, re.IGNORECASE)
                    if match:
                        try:
                            count = int(match.group(1))
                            if 2 <= count <= 500:
                                enriched.employee_count = count
                                enriched.employee_source = source
                                enriched.employee_evidence = match.group(0)
                                break
                        except ValueError:
                            continue

                # If we found something, stop looking
                if enriched.founder_name or enriched.employee_count:
                    break

        except Exception:
            continue


async def enrich_leads_batch(
    leads: list[RawEcommerceLead],
    batch_size: int = 10,
    timeout: float = 15.0,
) -> list[EnrichedEcommerceLead]:
    """Enrich a batch of leads."""
    enriched = []

    async with httpx.AsyncClient(
        timeout=timeout,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
        follow_redirects=True,
    ) as client:
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            tasks = [enrich_lead(client, lead) for lead in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, EnrichedEcommerceLead):
                    enriched.append(result)

            logger.info("  Enriched %d/%d", min(i + batch_size, len(leads)), len(leads))
            await asyncio.sleep(0.5)

    return enriched
