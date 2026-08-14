"""Contact recovery from official website only — never invent emails."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from collectors.extraction.public_contacts import extract_public_contacts
from revenue_data_acquisition.models.types import AttributedValue, UNKNOWN

ROLE_PREFIXES = ("info@", "sales@", "hello@", "contact@", "support@", "founder@", "ceo@", "team@")

# Module 6 paths — official site only
CONTACT_PATHS = (
    "",
    "/about",
    "/about-us",
    "/company",
    "/team",
    "/leadership",
    "/contact",
    "/contact-us",
    "/careers",
    "/customers",
    "/pricing",
    "/solutions",
    "/industries",
    "/press",
)


class ContactRecoveryEngine:
    def recover(self, website: str, *, collector: str = UNKNOWN, timeout: float = 6.0, max_pages: int = 6) -> list[AttributedValue]:
        if not website:
            return []
        if not str(website).startswith("http"):
            website = f"https://{website}"
        parsed = urlparse(website)
        domain = parsed.netloc.lower().removeprefix("www.")
        if not domain:
            return []
        base = f"{parsed.scheme}://{parsed.netloc}"
        emails: list[str] = []
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "BeaconRDAP/1.0 (+https://beacon.ai)"},
            ) as client:
                pages = 0
                for path in CONTACT_PATHS:
                    if pages >= max_pages:
                        break
                    url = base if not path else urljoin(base + "/", path.lstrip("/"))
                    try:
                        resp = client.get(url)
                    except Exception:  # noqa: BLE001
                        continue
                    if resp.status_code >= 400 or len(resp.text) < 40:
                        continue
                    pages += 1
                    hit = extract_public_contacts(resp.text, page_url=url, domain=domain)
                    for email in hit.get("emails") or []:
                        if email not in emails:
                            emails.append(email)
                    if emails:
                        break
        except Exception:  # noqa: BLE001
            pass

        now = datetime.now(UTC).isoformat()
        out: list[AttributedValue] = []

        def rank(email: str) -> int:
            low = email.lower()
            for i, p in enumerate(ROLE_PREFIXES):
                if low.startswith(p):
                    return i
            if "." in low.split("@")[0]:
                return 50
            return 80

        for email in sorted(emails, key=rank):
            out.append(
                AttributedValue(
                    value=email,
                    source="company_website",
                    collector=collector,
                    confidence=92.0 if any(email.lower().startswith(p) for p in ROLE_PREFIXES) else 85.0,
                    verified=True,
                    verified_at=now,
                    evidence=["same_domain_email", f"website:{website}"],
                )
            )
        return out[:5]

    def recover_from_payload(self, payload: dict[str, Any]) -> list[AttributedValue]:
        website = payload.get("official_website") or payload.get("website")
        return self.recover(str(website or ""), collector=str(payload.get("source") or UNKNOWN))
