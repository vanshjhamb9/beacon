"""Email Verification Engine - Verify email addresses deterministically."""

from __future__ import annotations

import re

from packages.sales_intelligence_platform.models import ContactChannel

DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
LOCAL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+\-]+$')


def verify_emails(channels: list[ContactChannel]) -> list[ContactChannel]:
    """Verify all email channels."""
    for ch in channels:
        if ch.kind.endswith("_email"):
            _verify_single_email(ch)
    return channels


def _verify_single_email(ch: ContactChannel) -> None:
    """Verify a single email channel."""
    email = ch.value.strip().lower()

    if not email or "@" not in email:
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        return

    parts = email.split("@")
    if len(parts) != 2:
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        return

    local, domain = parts

    # Format validation
    if not LOCAL_PATTERN.match(local) or not DOMAIN_PATTERN.match(domain):
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        ch.evidence.append("Email format validation failed")
        return

    # Role-based email detection
    role_prefixes = {"info", "hello", "contact", "support", "sales", "admin", "web", "office", "team"}
    if local in role_prefixes:
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.75, ch.confidence)
        ch.evidence.append(f"Role-based email: {local}@")
        return

    # Business domain check
    if ch.source == "website" and domain == ch.value.split("@")[1]:
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.85, ch.confidence + 0.1)
        ch.evidence.append("Email from company website")
        return

    ch.verification_level = "UNVERIFIED"
