from __future__ import annotations

import re

from lead_enrichment.models.types import (
    ContactEntry,
    ContactKind,
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    WebsiteFetchResult,
)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)?\d{3,4}[\s\-.]?\d{3,4}"
)
_ROLE_PREFIXES = ("info@", "hello@", "contact@", "sales@", "support@", "team@", "press@", "careers@")


class ContactExtractor:
    def extract(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None,
    ) -> list[ContactEntry]:
        contacts: list[ContactEntry] = []
        seen: set[str] = set()

        attrs = item.company_attributes
        for key, kind in (
            ("company_email", ContactKind.COMPANY_EMAIL),
            ("public_email", ContactKind.COMPANY_EMAIL),
            ("role_email", ContactKind.ROLE_BASED_EMAIL),
            ("phone", ContactKind.BUSINESS_PHONE),
            ("business_phone", ContactKind.BUSINESS_PHONE),
        ):
            value = attrs.get(key)
            if isinstance(value, str) and value.strip():
                normalized = value.strip()
                if normalized.lower() in seen:
                    continue
                seen.add(normalized.lower())
                contacts.append(
                    ContactEntry(
                        kind=kind,
                        value=normalized,
                        label=key,
                        confidence=95.0,
                        source=EnrichmentSourceType.USER_PROVIDED,
                        is_public=True,
                    )
                )

        if not website:
            return contacts

        for page in website.pages:
            if page.page_type not in {"homepage", "contact", "about", "footer", "privacy", "team"}:
                if page.page_type not in {"careers", "terms"}:
                    continue
            for email in _EMAIL_RE.findall(page.html):
                lowered = email.lower()
                if lowered in seen or lowered.endswith((".png", ".jpg", ".gif", ".svg")):
                    continue
                if "example.com" in lowered or "sentry" in lowered or "wixpress" in lowered:
                    continue
                seen.add(lowered)
                kind = (
                    ContactKind.ROLE_BASED_EMAIL
                    if any(lowered.startswith(prefix) for prefix in _ROLE_PREFIXES)
                    else ContactKind.COMPANY_EMAIL
                )
                contacts.append(
                    ContactEntry(
                        kind=kind,
                        value=lowered,
                        label=page.page_type,
                        confidence=84.0 if page.page_type == "contact" else 72.0,
                        source=EnrichmentSourceType.COMPANY_WEBSITE,
                        source_url=page.url,
                        is_public=True,
                    )
                )

            if page.page_type in {"contact", "homepage", "about"}:
                for phone in _PHONE_RE.findall(page.text):
                    digits = re.sub(r"\D", "", phone)
                    if len(digits) < 8 or len(digits) > 15:
                        continue
                    if digits in seen:
                        continue
                    seen.add(digits)
                    contacts.append(
                        ContactEntry(
                            kind=ContactKind.BUSINESS_PHONE,
                            value=phone.strip(),
                            label=page.page_type,
                            confidence=70.0,
                            source=EnrichmentSourceType.COMPANY_WEBSITE,
                            source_url=page.url,
                            is_public=True,
                        )
                    )
        return contacts
