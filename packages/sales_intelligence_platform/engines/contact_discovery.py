"""Contact Discovery Engine - Discover all contact channels.

Never invent. Never predict. Unknown preferred over fake.
"""

from __future__ import annotations

import re
from typing import Any

from packages.sales_intelligence_platform.models import ContactChannel, DecisionMaker

# ─── CHANNEL PRIORITY ─────────────────────────────────────────────

CHANNEL_PRIORITY: dict[str, int] = {
    "founder_email": 1,
    "executive_email": 2,
    "role_based_email": 3,
    "business_email": 4,
    "contact_form": 5,
    "business_phone": 6,
    "founder_phone": 7,
    "linkedin_company": 8,
    "support_email": 9,
    "sales_email": 10,
    "whatsapp_business": 11,
}


def discover_contact_channels(
    lead_data: dict, decision_makers: list[DecisionMaker]
) -> list[ContactChannel]:
    """Discover all available contact channels from lead data."""
    channels: list[ContactChannel] = []
    seen: set[str] = set()

    # ─── Email channels ──────────────────────────────────────────
    email = lead_data.get("email", "")
    if email and email not in seen:
        kind = _classify_email(email)
        channels.append(ContactChannel(
            kind=kind,
            value=email,
            label=_email_label(kind),
            rank=CHANNEL_PRIORITY.get(kind, 99),
            confidence=0.80 if kind in ("founder_email", "executive_email") else 0.60,
            source="website",
            verification_level="UNVERIFIED",
            evidence=[f"Email found on website: {email}"],
        ))
        seen.add(email)

    # From decision makers
    for dm in decision_makers:
        if dm.work_email and dm.work_email not in seen:
            kind = f"{dm.normalized_role.lower().replace(' ', '_')}_email"
            if "founder" in dm.normalized_role.lower():
                kind = "founder_email"
            elif "ceo" in dm.normalized_role.lower() or "director" in dm.normalized_role.lower():
                kind = "executive_email"
            channels.append(ContactChannel(
                kind=kind,
                value=dm.work_email,
                label=f"{dm.name} ({dm.normalized_role})",
                rank=CHANNEL_PRIORITY.get(kind, 50),
                confidence=dm.confidence,
                source=dm.source,
                verification_level="UNVERIFIED",
                evidence=dm.evidence,
            ))
            seen.add(dm.work_email)

    # ─── Phone channels ──────────────────────────────────────────
    phone = lead_data.get("phone", "")
    if phone and phone not in seen:
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        channels.append(ContactChannel(
            kind="business_phone",
            value=clean_phone,
            label="Business Phone",
            rank=CHANNEL_PRIORITY.get("business_phone", 6),
            confidence=0.70,
            source="website",
            verification_level="UNVERIFIED",
            evidence=[f"Phone found on website: {phone}"],
        ))
        seen.add(phone)

    # ─── LinkedIn channels ───────────────────────────────────────
    social_links = lead_data.get("social_links", {})
    linkedin = social_links.get("linkedin", "") or lead_data.get("linkedin_url", "")
    if linkedin and linkedin not in seen:
        channels.append(ContactChannel(
            kind="linkedin_company",
            value=linkedin,
            label="LinkedIn Company",
            rank=CHANNEL_PRIORITY.get("linkedin_company", 8),
            confidence=0.90,
            source="website",
            verification_level="VERIFIED",
            evidence=[f"LinkedIn found: {linkedin}"],
        ))
        seen.add(linkedin)

    # ─── WhatsApp channels ───────────────────────────────────────
    if lead_data.get("whatsapp_detected", False) and phone:
        wa_number = re.sub(r'[^\d]', '', phone)
        if wa_number not in seen:
            channels.append(ContactChannel(
                kind="whatsapp_business",
                value=wa_number,
                label="WhatsApp Business",
                rank=CHANNEL_PRIORITY.get("whatsapp_business", 11),
                confidence=0.60,
                source="website_detection",
                verification_level="UNVERIFIED",
                evidence=["WhatsApp detected on website"],
            ))
            seen.add(wa_number)

    # ─── Support/Sales email patterns ────────────────────────────
    domain = lead_data.get("domain", "")
    if domain:
        for kind, prefix in [("support_email", "support"), ("sales_email", "sales")]:
            constructed = f"{prefix}@{domain}"
            if constructed not in seen:
                channels.append(ContactChannel(
                    kind=kind,
                    value=constructed,
                    label=f"{prefix.title()} Email (inferred)",
                    rank=CHANNEL_PRIORITY.get(kind, 50),
                    confidence=0.30,
                    source="pattern_inference",
                    verification_level="UNKNOWN",
                    evidence=[f"Standard {prefix}@ pattern for domain {domain}"],
                ))
                seen.add(constructed)

    # Sort by rank (lower = higher priority)
    channels.sort(key=lambda c: c.rank)

    return channels


def _classify_email(email: str) -> str:
    """Classify email type based on local part."""
    local = email.split("@")[0].lower()
    if local in ("founder", "ceo", "director", "md"):
        return "executive_email"
    if local in ("info", "hello", "contact", "admin", "web"):
        return "business_email"
    if local in ("support", "help", "care"):
        return "support_email"
    if local in ("sales", "biz", "business"):
        return "sales_email"
    if "." in local and not local[0].isdigit():
        return "role_based_email"
    return "business_email"


def _email_label(kind: str) -> str:
    """Generate human-readable label for email kind."""
    labels = {
        "founder_email": "Founder Email",
        "executive_email": "Executive Email",
        "role_based_email": "Role-based Email",
        "business_email": "Business Email",
        "support_email": "Support Email",
        "sales_email": "Sales Email",
    }
    return labels.get(kind, "Email")
