from __future__ import annotations

import re
from urllib.parse import urlparse

from lead_enrichment.models.types import (
    ContactEntry,
    ContactKind,
    EnrichedCompanyProfile,
    PersonEntry,
    SocialProfileEntry,
    TechnologyEntry,
)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_PHONE_DIGITS_RE = re.compile(r"\d+")


class EnrichmentValidator:
    def validate_profile(self, profile: EnrichedCompanyProfile) -> EnrichedCompanyProfile:
        website = profile.website
        if website and not self._valid_http_url(website):
            website = None
        domain = profile.domain
        if domain and ("/" in domain or " " in domain):
            domain = None
        founded = profile.founded_year
        if founded is not None and not (1800 <= founded <= 2100):
            founded = None
        employee_count = profile.employee_count_estimate
        if employee_count is not None and employee_count <= 0:
            employee_count = None
        return profile.model_copy(
            update={
                "website": website,
                "domain": domain,
                "founded_year": founded,
                "employee_count_estimate": employee_count,
            }
        )

    def validate_contacts(self, contacts: list[ContactEntry]) -> list[ContactEntry]:
        valid: list[ContactEntry] = []
        seen: set[str] = set()
        for contact in contacts:
            value = contact.value.strip()
            if contact.kind in {ContactKind.COMPANY_EMAIL, ContactKind.ROLE_BASED_EMAIL}:
                if not _EMAIL_RE.match(value):
                    continue
                value = value.lower()
            elif contact.kind == ContactKind.BUSINESS_PHONE:
                digits = "".join(_PHONE_DIGITS_RE.findall(value))
                if len(digits) < 8 or len(digits) > 15:
                    continue
            key = f"{contact.kind.value}:{value.lower()}"
            if key in seen:
                continue
            seen.add(key)
            valid.append(contact.model_copy(update={"value": value, "is_public": True}))
        return valid

    def validate_people(self, people: list[PersonEntry]) -> list[PersonEntry]:
        valid: list[PersonEntry] = []
        seen: set[str] = set()
        for person in people:
            name = person.name.strip()
            role = person.role.strip()
            if len(name) < 2 or len(role) < 2:
                continue
            key = f"{name.lower()}|{role.lower()}"
            if key in seen:
                continue
            seen.add(key)
            linkedin = person.linkedin_url
            if linkedin and not self._valid_http_url(linkedin):
                linkedin = None
            email = person.work_email.lower().strip() if person.work_email else None
            if email and not _EMAIL_RE.match(email):
                email = None
            valid.append(person.model_copy(update={"name": name, "role": role, "linkedin_url": linkedin, "work_email": email}))
        return valid

    def validate_technologies(self, technologies: list[TechnologyEntry]) -> list[TechnologyEntry]:
        valid: list[TechnologyEntry] = []
        seen: set[str] = set()
        for tech in technologies:
            name = tech.name.strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            confidence = min(100.0, max(0.0, tech.confidence))
            valid.append(tech.model_copy(update={"name": name, "confidence": confidence}))
        return valid

    def validate_social(self, profiles: list[SocialProfileEntry]) -> list[SocialProfileEntry]:
        valid: list[SocialProfileEntry] = []
        seen: set[str] = set()
        for profile in profiles:
            if not self._valid_http_url(profile.url):
                continue
            key = profile.platform.lower()
            if key in seen and profile.confidence < 80:
                continue
            seen.add(key)
            valid.append(profile)
        return valid

    def _valid_http_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
