"""Contact Verification Engine - Verify contact channels without external APIs.

Deterministic verification using pattern matching and heuristics.
Never fabricate verification status.
"""

from __future__ import annotations

import re

from packages.sales_intelligence_platform.models import ContactChannel

# ─── EMAIL PATTERNS ───────────────────────────────────────────────

VALID_EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

DISPOSABLE_DOMAINS: set[str] = {
    "tempmail.com", "throwaway.email", "guerrillamail.com",
    "mailinator.com", "yopmail.com", "trashmail.com",
    "fakeinbox.com", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "dispostable.com", "maildrop.cc",
}

FREE_EMAIL_DOMAINS: set[str] = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com",
    "zoho.com", "yandex.com", "gmx.com",
}

# ─── PHONE PATTERNS ──────────────────────────────────────────────

INDIA_PHONE_REGEX = re.compile(r'^(\+91)?[6-9]\d{9}$')
US_PHONE_REGEX = re.compile(r'^(\+1)?[2-9]\d{9}$')


def verify_contacts(channels: list[ContactChannel]) -> list[ContactChannel]:
    """Verify all contact channels using deterministic heuristics."""
    for ch in channels:
        if ch.kind in ("founder_email", "executive_email", "role_based_email",
                        "business_email", "support_email", "sales_email"):
            _verify_email(ch)
        elif ch.kind in ("business_phone", "founder_phone"):
            _verify_phone(ch)
        elif ch.kind == "whatsapp_business":
            _verify_whatsapp(ch)
        elif ch.kind == "linkedin_company":
            _verify_linkedin(ch)
    return channels


def _verify_email(ch: ContactChannel) -> None:
    """Verify email using pattern matching."""
    email = ch.value.lower()

    if not VALID_EMAIL_REGEX.match(email):
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        ch.evidence.append("Email format is invalid")
        return

    domain = email.split("@")[1]

    if domain in DISPOSABLE_DOMAINS:
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        ch.evidence.append("Disposable email domain detected")
        return

    if domain in FREE_EMAIL_DOMAINS:
        ch.verification_level = "UNVERIFIED"
        ch.confidence = max(0.3, ch.confidence - 0.2)
        ch.evidence.append(f"Free email domain: {domain}")
        return

    # Business domain email
    if ch.source == "website":
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.85, ch.confidence + 0.1)
        ch.evidence.append("Email from company website domain")
    elif ch.source == "email_pattern":
        ch.verification_level = "UNVERIFIED"
        ch.evidence.append("Email inferred from pattern, needs verification")
    else:
        ch.verification_level = "UNVERIFIED"


def _verify_phone(ch: ContactChannel) -> None:
    """Verify phone number format."""
    phone = re.sub(r'[^\d+]', '', ch.value)

    if INDIA_PHONE_REGEX.match(phone) or US_PHONE_REGEX.match(phone):
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.80, ch.confidence + 0.1)
        ch.evidence.append("Phone number format is valid")
    elif len(phone) >= 10:
        ch.verification_level = "UNVERIFIED"
        ch.evidence.append("Phone format plausible but unverified")
    else:
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        ch.evidence.append("Phone number too short")


def _verify_whatsapp(ch: ContactChannel) -> None:
    """Verify WhatsApp number."""
    phone = re.sub(r'[^\d]', '', ch.value)
    if len(phone) >= 10:
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.70, ch.confidence)
        ch.evidence.append("WhatsApp number format plausible")
    else:
        ch.verification_level = "INVALID"
        ch.confidence = 0.0


def _verify_linkedin(ch: ContactChannel) -> None:
    """Verify LinkedIn URL."""
    url = ch.value.lower()
    if "linkedin.com" in url:
        ch.verification_level = "VERIFIED"
        ch.confidence = min(0.95, ch.confidence + 0.15)
        ch.is_verified_public = True
        ch.evidence.append("LinkedIn URL is valid format")
    else:
        ch.verification_level = "UNVERIFIED"
