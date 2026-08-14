"""Phone Validation Engine - Validate and classify phone numbers."""

from __future__ import annotations

import re

from packages.sales_intelligence_platform.models import ContactChannel

INDIA_MOBILE = re.compile(r'^(\+91)?[6-9]\d{9}$')
INDIA_LANDLINE = re.compile(r'^(\+91)?[0-4]\d{8,9}$')
US_PHONE = re.compile(r'^(\+1)?[2-9]\d{9}$')
GENERIC_PHONE = re.compile(r'^\+?\d{7,15}$')


def validate_phones(channels: list[ContactChannel]) -> list[ContactChannel]:
    """Validate and classify all phone channels."""
    for ch in channels:
        if ch.kind in ("business_phone", "founder_phone", "whatsapp_business"):
            _validate_single_phone(ch)
    return channels


def _validate_single_phone(ch: ContactChannel) -> None:
    """Validate a single phone channel."""
    raw = ch.value.strip()
    phone = re.sub(r'[^\d+]', '', raw)

    if not phone:
        ch.verification_level = "INVALID"
        ch.confidence = 0.0
        return

    # Remove leading + or 00
    digits = phone.lstrip("+").lstrip("00")

    if INDIA_MOBILE.match(digits):
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.80, ch.confidence + 0.1)
        ch.evidence.append("Valid Indian mobile number format")
        return

    if INDIA_LANDLINE.match(digits):
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.75, ch.confidence + 0.05)
        ch.evidence.append("Valid Indian landline format")
        return

    if US_PHONE.match(digits):
        ch.verification_level = "LIKELY"
        ch.confidence = min(0.80, ch.confidence + 0.1)
        ch.evidence.append("Valid US phone format")
        return

    if GENERIC_PHONE.match(digits) and len(digits) >= 10:
        ch.verification_level = "UNVERIFIED"
        ch.evidence.append("Phone format plausible but unverified")
        return

    ch.verification_level = "INVALID"
    ch.confidence = 0.0
    ch.evidence.append("Phone number format invalid")
