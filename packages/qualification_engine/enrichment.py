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

# True WhatsApp *bot/automation* vendors — NOT a simple wa.me chat link
WHATSAPP_BOT_SIGNATURES = (
    "wati.io",
    "wati.com",
    "interakt",
    "aisensy",
    "ai sensy",
    "gallabox",
    "doubletick",
    "gupshup",
    "360dialog",
    "maytapi",
    "respond.io",
    "yellow.ai",
    "yellowai",
    "haptik",
    "verloop",
    "limechat",
    "zoko.io",
    "getzoko",
    "whatsapp business api",
    "waba",
    "cloud api whatsapp",
)

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

# Indian mid-D2C growth / ads / ops stack — homepage + careers HTML signatures
TECH_STACK_SIGNATURES: dict[str, tuple[str, ...]] = {
    "meta_pixel": ("fbevents.js", "connect.facebook.net", "fbq(", "facebook.net/tr"),
    "google_ads": ("googleadservices", "gtag/js?id=aw-", "google_conversion_id"),
    "gtm": ("googletagmanager.com/gtm.js", "gtm.js?id=gtm-"),
    "klaviyo": ("klaviyo.com", "static.klaviyo.com", "_learnq"),
    "shiprocket": ("shiprocket", "sr-cdn"),
    "razorpay": ("checkout.razorpay", "razorpay.com"),
    "judgeme": ("judge.me", "judgeme"),
    "gorgias": ("gorgias.chat", "gorgias.com"),
    "yotpo": ("yotpo.com", "staticw2.yotpo"),
    "whatsapp_business_api": ("whatsapp business api", "graph.facebook.com", "waba"),
}

GROWTH_SIGNAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "hiring": re.compile(
        r"(we[''']?re hiring|join our team|open positions|/careers\b|/jobs\b|"
        r"hiring (?:for|a|an)|work with us|now hiring|career opportunities|"
        r"we're growing our team|looking for (?:a|an|engineers?|developers?|founders?)|"
        r"seeking (?:a|an|engineers?|developers?)|we need (?:a|an|engineers?|developers?)|"
        r"team (?:is )?growing|come work|we're (?:a )?team|"
        r"founding engineer|cto hire|head of (?:engineering|product|technology))",
        re.IGNORECASE,
    ),
    "funding": re.compile(
        r"(series [a-d]\b|seed round|raised\s*(?:\$|₹|inr|usd)?\s*[\d.,]+|"
        r"backed by|venture capital|funding round|investors? include)",
        re.IGNORECASE,
    ),
    "expansion": re.compile(
        r"(expanding to|new (?:store|flagship)|now available in|launching in|"
        r"opened in|pan[- ]india)",
        re.IGNORECASE,
    ),
    "new_products": re.compile(
        r"(just launched|new launch|introducing (?:our|the)|new collection|"
        r"now live|fresh drop)",
        re.IGNORECASE,
    ),
    "cx_hiring": re.compile(
        r"(customer (?:support|success|experience|care) (?:executive|associate|manager|lead)|"
        r"hiring.{0,40}(?:support|cx|care)|whatsapp (?:support|agent))",
        re.IGNORECASE,
    ),
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

        # === WHATSAPP LINK vs BOT ===
        # Simple wa.me / "whatsapp" chat links are NOT buying signals for COMAI.
        # Only true WhatsApp bot/automation vendors are recorded (optional soft cue).
        whatsapp_bot_found = [s for s in WHATSAPP_BOT_SIGNATURES if s in body_lower]
        whatsapp_link_found = [s for s in WHATSAPP_SIGNATURES if s in body_lower]
        if whatsapp_bot_found:
            enriched.whatsapp_state = DetectionState.VERIFIED_PRESENT
            enriched.whatsapp_evidence = f"WhatsApp bot/automation: {', '.join(whatsapp_bot_found[:3])}"
            enriched.whatsapp_source = "homepage_html"
        elif whatsapp_link_found:
            # Link/widget only — ignore for ranking (not a bot)
            enriched.whatsapp_state = DetectionState.VERIFIED_ABSENT
            enriched.whatsapp_evidence = (
                f"WhatsApp chat link only (not a bot): {', '.join(whatsapp_link_found[:2])}"
            )
            enriched.whatsapp_source = "homepage_html"
        else:
            enriched.whatsapp_state = DetectionState.VERIFIED_ABSENT
            enriched.whatsapp_evidence = "Checked homepage HTML — no WhatsApp bot signatures found"
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

        # === TECH STACK + GROWTH / BUYING INTENT ===
        _extract_tech_stack(enriched, body_lower)
        _extract_growth_signals(enriched, body, source="homepage_html")
        _derive_buying_signals(enriched)

        # === DESCRIPTION ===
        desc_match = re.search(
            r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
            body, re.IGNORECASE
        )
        if desc_match:
            lead.description = desc_match.group(1)[:500]

        # === EMPLOYEE COUNT (from About page) ===
        await _extract_about_page_info(client, lead, enriched)

        # === CAREERS / PRESS intent pages (hiring + funding) ===
        await _probe_intent_pages(client, lead, enriched)

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
        f"{base}/contact-us",
        f"{base}/get-in-touch",
        f"{base}/support",
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
    # Also try team/about pages for founder emails
    team_urls = [
        f"{base}/team",
        f"{base}/about",
        f"{base}/about-us",
        f"{base}/our-team",
    ]
    for url in team_urls:
        try:
            resp = await client.get(url, follow_redirects=True, timeout=10.0)
            if resp.status_code != 200:
                continue
            _extract_contacts(enriched, resp.text, source="team_page")
            _extract_founder_name(enriched, resp.text, source="team_page")
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


def _extract_tech_stack(enriched: EnrichedEcommerceLead, body_lower: str) -> None:
    """Detect ads / ops / commerce stack signatures used for intent ranking."""
    found: list[str] = []
    if enriched.platform:
        found.append(enriched.platform)
    for name, signatures in TECH_STACK_SIGNATURES.items():
        if any(sig in body_lower for sig in signatures):
            found.append(name)
    # True WhatsApp bot only (links ignored)
    if any(sig in body_lower for sig in WHATSAPP_BOT_SIGNATURES):
        found.append("whatsapp_bot")
    # de-dupe preserve order
    enriched.technologies = list(dict.fromkeys(found))


def _append_growth_signal(
    enriched: EnrichedEcommerceLead,
    *,
    signal_type: str,
    evidence: str,
    confidence: float,
    source: str,
) -> None:
    existing = {
        (str(s.get("type") or ""), str(s.get("evidence") or "")[:60])
        for s in (enriched.growth_signals or [])
        if isinstance(s, dict)
    }
    key = (signal_type, evidence[:60])
    if key in existing:
        return
    enriched.growth_signals.append(
        {
            "type": signal_type,
            "evidence": evidence[:160],
            "confidence": round(min(0.95, max(0.4, confidence)), 2),
            "source": source,
        }
    )


def _extract_growth_signals(
    enriched: EnrichedEcommerceLead,
    html: str,
    *,
    source: str,
) -> None:
    """Extract hiring / funding / expansion / launch cues from HTML text."""
    for signal_type, pattern in GROWTH_SIGNAL_PATTERNS.items():
        match = pattern.search(html)
        if not match:
            continue
        # cx_hiring is a specialized hiring cue
        mapped = "hiring" if signal_type == "cx_hiring" else signal_type
        conf = 0.85 if signal_type == "cx_hiring" else 0.75
        if source.startswith("careers"):
            conf = min(0.95, conf + 0.1)
        _append_growth_signal(
            enriched,
            signal_type=mapped,
            evidence=match.group(0).strip()[:120],
            confidence=conf,
            source=source,
        )

    # Ads active = growth via paid acquisition
    techs = {t.lower() for t in (enriched.technologies or [])}
    if techs & {"meta_pixel", "google_ads", "gtm"}:
        _append_growth_signal(
            enriched,
            signal_type="advertising",
            evidence="Paid ads stack detected: " + ", ".join(sorted(techs & {"meta_pixel", "google_ads", "gtm"})),
            confidence=0.8,
            source=source,
        )


def _derive_buying_signals(enriched: EnrichedEcommerceLead) -> None:
    """Compose COMAI-relevant buying intent from stack + gaps + growth."""
    buying: list[dict[str, Any]] = list(enriched.buying_signals or [])
    seen = {str(b.get("type") or "") for b in buying if isinstance(b, dict)}

    def add(signal_type: str, evidence: str, confidence: float) -> None:
        if signal_type in seen:
            return
        seen.add(signal_type)
        buying.append(
            {
                "type": signal_type,
                "evidence": evidence[:160],
                "confidence": confidence,
                "source": "derived",
            }
        )

    chat = str(enriched.chatbot_state or "").upper()
    techs = {t.lower() for t in (enriched.technologies or [])}
    growth_types = {
        str(g.get("type") or "")
        for g in (enriched.growth_signals or [])
        if isinstance(g, dict)
    }
    pain_types = {
        str(p.get("type") or "")
        for p in (enriched.pain_points or [])
        if isinstance(p, dict)
    }
    has_wa_bot = "whatsapp_bot" in techs or (
        "PRESENT" in str(enriched.whatsapp_state or "").upper()
        and "bot" in str(enriched.whatsapp_evidence or "").lower()
    )

    # Ignore WhatsApp *chat links* — intent is chatbot automation + growth + ops
    if "ABSENT" in chat and (techs & {"meta_pixel", "google_ads", "shopify", "woocommerce", "gtm"}):
        add("automation_gap_on_ads_brand", "Growing commerce/ads brand without chatbot automation", 0.9)
    if "ABSENT" in chat and ("return_policy" in pain_types or "cod_available" in pain_types):
        add("ops_support_gap", "Returns/COD friction without chatbot coverage", 0.82)
    if "hiring" in growth_types and "ABSENT" in chat:
        add("hiring_with_support_gap", "Hiring while support automation gap exists", 0.92)
    if "funding" in growth_types:
        add("recent_funding_window", "Funding / investor signal on site", 0.85)
    if techs & {"shiprocket", "razorpay", "klaviyo"} and "ABSENT" in chat:
        add("ops_stack_without_automation", "Ops/CRM stack present but no chatbot automation", 0.78)
    if has_wa_bot and "ABSENT" in chat:
        add("wa_bot_without_web_chat", "Has WhatsApp bot vendor but no web chatbot", 0.55)

    enriched.buying_signals = buying


async def _probe_intent_pages(
    client: httpx.AsyncClient,
    lead: RawEcommerceLead,
    enriched: EnrichedEcommerceLead,
) -> None:
    """Light fan-out to careers/press pages for hiring + funding intent."""
    base = (lead.website or "").rstrip("/")
    if not base:
        return
    growth_types = {
        str(g.get("type") or "")
        for g in (enriched.growth_signals or [])
        if isinstance(g, dict)
    }
    # Skip if we already have both hiring and funding
    if "hiring" in growth_types and "funding" in growth_types:
        return

    paths = (
        "/pages/careers",
        "/careers",
        "/pages/jobs",
        "/jobs",
        "/open-positions",
        "/hiring",
        "/team",
        "/#team",
        "/blogs/news",
        "/blogs/press",
        "/pages/press",
    )
    for path in paths:
        try:
            resp = await client.get(f"{base}{path}", follow_redirects=True, timeout=8.0)
            if resp.status_code != 200 or len(resp.text) < 400:
                continue
            src = f"intent_page:{path}"
            _extract_growth_signals(enriched, resp.text, source=src)
            growth_types = {
                str(g.get("type") or "")
                for g in (enriched.growth_signals or [])
                if isinstance(g, dict)
            }
            if "hiring" in growth_types and "funding" in growth_types:
                break
        except Exception:  # noqa: BLE001
            continue
    # Refresh derived buying signals after page probes
    _derive_buying_signals(enriched)


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
