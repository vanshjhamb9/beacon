"""Contact Recovery Engine v2 — public page evidence only. Never invent people."""

from __future__ import annotations

import re
from typing import Any

from company_intelligence.models.types import ContactPerson, WebsiteCorpus

ROLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Founder", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:Co-?Founder|Founder)\b")),
    ("CEO", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:CEO|Chief Executive Officer)\b")),
    ("CTO", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:CTO|Chief Technology Officer)\b")),
    ("VP Engineering", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:VP Engineering|Vice President of Engineering)\b")),
    ("Head of Product", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:Head of Product|VP Product)\b")),
    ("Operations", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:COO|Head of Operations|VP Operations)\b")),
    ("Marketing", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:CMO|Head of Marketing|VP Marketing)\b")),
    ("Sales", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:CRO|Head of Sales|VP Sales)\b")),
    ("Growth", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:Head of Growth|VP Growth)\b")),
    ("Innovation", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:Head of Innovation|Chief Innovation Officer)\b")),
    ("Digital Transformation", re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[,–\-—|]\s*(?:Head of Digital|Digital Transformation)\b")),
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+?\d[\d\-\s().]{7,}\d")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[A-Za-z0-9\-_/]+", re.I)

ROLE_FIRST: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Founder", re.compile(r"(?:Co-?Founder|Founder)\s*[,–\-—|:]\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)")),
    ("CEO", re.compile(r"(?:CEO|Chief Executive Officer)\s*[,–\-—|:]\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)")),
    ("CTO", re.compile(r"(?:CTO|Chief Technology Officer)\s*[,–\-—|:]\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)")),
)

STOP_NAMES = frozenset({"Learn More", "Get Started", "Contact Us", "Our Team", "Join Us", "Read More"})


class ContactRecoveryEngine:
    def recover(self, corpus: WebsiteCorpus, payload: dict[str, Any] | None = None) -> list[ContactPerson]:
        payload = payload or {}
        people: list[ContactPerson] = []

        for raw in payload.get("decision_makers") or payload.get("contacts") or []:
            if isinstance(raw, dict) and raw.get("name"):
                people.append(
                    ContactPerson(
                        name=str(raw["name"]),
                        role=str(raw.get("role") or "UNKNOWN"),
                        profile=str(raw.get("profile") or raw.get("linkedin") or "UNKNOWN"),
                        email=str(raw.get("email") or "UNKNOWN"),
                        phone=str(raw.get("phone") or "UNKNOWN"),
                        confidence=float(raw.get("confidence") or 90),
                        source=str(raw.get("source") or "payload"),
                        evidence=list(raw.get("evidence") or ["payload_contact"]),
                    )
                )

        team_pages = [
            p
            for p in corpus.pages
            if any(x in p.path.lower() for x in ("/team", "/about", "/leadership", "/company", "/contact"))
        ] or corpus.pages[:3]

        for page in team_pages:
            text = f"{page.title}\n{' '.join(page.headings)}\n{page.text}"
            for role, pattern in (*ROLE_PATTERNS, *ROLE_FIRST):
                for m in pattern.finditer(text):
                    name = m.group(1).strip()
                    if name in STOP_NAMES or len(name) < 3:
                        continue
                    people.append(
                        ContactPerson(
                            name=name,
                            role=role,
                            profile="UNKNOWN",
                            confidence=78.0,
                            source="website_team_page",
                            evidence=[f"page:{page.path}", f"role:{role}", f"match:{m.group(0)[:80]}"],
                        )
                    )
            for li in LINKEDIN_RE.findall(text)[:5]:
                if "/company/" in li:
                    continue
                slug = li.rstrip("/").split("/")[-1].replace("-", " ").title()
                if slug and slug not in STOP_NAMES:
                    people.append(
                        ContactPerson(
                            name=slug,
                            role="UNKNOWN",
                            profile=li,
                            confidence=60.0,
                            source="linkedin_public_ref",
                            evidence=[f"linkedin:{li}", f"page:{page.path}"],
                        )
                    )
            for email in EMAIL_RE.findall(text)[:5]:
                if any(x in email.lower() for x in ("example.com", "sentry.io", "wixpress", "schema.org")):
                    continue
                people.append(
                    ContactPerson(
                        name="UNKNOWN",
                        role="Business Email",
                        email=email,
                        confidence=85.0,
                        source="website_contact",
                        evidence=[f"email:{email}", f"page:{page.path}"],
                    )
                )
            for phone in PHONE_RE.findall(text)[:3]:
                cleaned = re.sub(r"\s+", " ", phone).strip()
                if len(re.sub(r"\D", "", cleaned)) < 8:
                    continue
                people.append(
                    ContactPerson(
                        name="UNKNOWN",
                        role="Phone",
                        phone=cleaned,
                        confidence=70.0,
                        source="website_contact",
                        evidence=[f"phone:{cleaned}", f"page:{page.path}"],
                    )
                )

        return self._dedupe(people)[:20]

    def _dedupe(self, people: list[ContactPerson]) -> list[ContactPerson]:
        seen: set[str] = set()
        out: list[ContactPerson] = []
        for p in people:
            key = f"{p.name.lower()}|{p.role.lower()}|{p.email.lower()}"
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out
