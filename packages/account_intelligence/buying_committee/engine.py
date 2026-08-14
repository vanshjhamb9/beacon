from __future__ import annotations

from datetime import UTC, datetime
import re

from account_intelligence.models.types import (
    AccountIntelligenceInput,
    CommitteeMember,
    CommitteeRole,
    ContactValidationResult,
    ObservedContact,
)


ROLE_AUTHORITY: dict[str, tuple[float, float, int]] = {
    CommitteeRole.FOUNDER.value: (95.0, 95.0, 100),
    CommitteeRole.CEO.value: (95.0, 95.0, 100),
    CommitteeRole.CTO.value: (85.0, 80.0, 90),
    CommitteeRole.COO.value: (80.0, 75.0, 85),
    CommitteeRole.CIO.value: (80.0, 75.0, 85),
    CommitteeRole.VP_ENGINEERING.value: (75.0, 70.0, 80),
    CommitteeRole.ENGINEERING_MANAGER.value: (60.0, 55.0, 65),
    CommitteeRole.HEAD_OF_AI.value: (70.0, 65.0, 75),
    CommitteeRole.PRODUCT_MANAGER.value: (65.0, 60.0, 70),
    CommitteeRole.HEAD_OF_OPERATIONS.value: (70.0, 65.0, 75),
    CommitteeRole.MARKETING_HEAD.value: (65.0, 60.0, 70),
    CommitteeRole.SALES_HEAD.value: (70.0, 65.0, 75),
    CommitteeRole.CUSTOMER_SUCCESS.value: (55.0, 50.0, 60),
    CommitteeRole.SUPPORT_HEAD.value: (55.0, 50.0, 60),
    CommitteeRole.FINANCE_HEAD.value: (75.0, 70.0, 80),
    CommitteeRole.HR_HEAD.value: (50.0, 45.0, 55),
    CommitteeRole.LEGAL.value: (60.0, 55.0, 65),
    CommitteeRole.IT_MANAGER.value: (60.0, 55.0, 65),
}

ROLE_ALIASES: list[tuple[str, str]] = [
    ("founder", CommitteeRole.FOUNDER.value),
    ("ceo", CommitteeRole.CEO.value),
    ("chief executive", CommitteeRole.CEO.value),
    ("cto", CommitteeRole.CTO.value),
    ("chief technology", CommitteeRole.CTO.value),
    ("coo", CommitteeRole.COO.value),
    ("cio", CommitteeRole.CIO.value),
    ("vp engineering", CommitteeRole.VP_ENGINEERING.value),
    ("engineering manager", CommitteeRole.ENGINEERING_MANAGER.value),
    ("head of ai", CommitteeRole.HEAD_OF_AI.value),
    ("product manager", CommitteeRole.PRODUCT_MANAGER.value),
    ("head of operations", CommitteeRole.HEAD_OF_OPERATIONS.value),
    ("marketing", CommitteeRole.MARKETING_HEAD.value),
    ("sales head", CommitteeRole.SALES_HEAD.value),
    ("head of sales", CommitteeRole.SALES_HEAD.value),
    ("customer success", CommitteeRole.CUSTOMER_SUCCESS.value),
    ("support", CommitteeRole.SUPPORT_HEAD.value),
    ("finance", CommitteeRole.FINANCE_HEAD.value),
    ("hr ", CommitteeRole.HR_HEAD.value),
    ("legal", CommitteeRole.LEGAL.value),
    ("it manager", CommitteeRole.IT_MANAGER.value),
]


class BuyingCommitteeEngine:
    """Discover public business contacts only — never invent people or PII."""

    def discover(self, item: AccountIntelligenceInput) -> list[CommitteeMember]:
        now = item.now or datetime.now(UTC)
        out: list[CommitteeMember] = []
        for obs in item.observed_contacts:
            if not obs.full_name.strip():
                continue
            role = self._normalize_role(obs.role) or (obs.role or "Unknown")
            influence, authority, priority = ROLE_AUTHORITY.get(role, (40.0, 35.0, 40))
            conf = 50.0
            if obs.business_email:
                conf += 15.0
            if obs.linkedin_url:
                conf += 15.0
            if obs.role:
                conf += 10.0
            out.append(
                CommitteeMember(
                    full_name=obs.full_name.strip(),
                    role=role,
                    department=obs.department,
                    business_email=obs.business_email,
                    business_phone=obs.business_phone,
                    linkedin_url=obs.linkedin_url,
                    company_profile_url=obs.company_profile_url,
                    confidence=min(95.0, conf),
                    verification="observed",
                    source=obs.source,
                    last_verified=obs.observed_at or now,
                    priority=priority,
                    influence_score=influence,
                    decision_authority=authority,
                    evidence=list(obs.evidence) + [f"source:{obs.source}", "fabricated:false"],
                    fabricated=False,
                )
            )
        out.sort(key=lambda m: (-m.priority, -m.confidence, m.full_name))
        return out

    def _normalize_role(self, role: str | None) -> str | None:
        if not role:
            return None
        low = role.lower()
        for alias, canonical in ROLE_ALIASES:
            if alias in low:
                return canonical
        return role.strip()


class ContactValidationEngine:
    """Never invent contacts. Validate observed emails/phones only."""

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s().]{6,}$")

    def validate(self, contacts: list[ObservedContact], *, domain: str | None, now: datetime | None = None) -> list[ContactValidationResult]:
        now = now or datetime.now(UTC)
        domain = (domain or "").lower().lstrip("@")
        results: list[ContactValidationResult] = []
        for c in contacts:
            if not c.full_name.strip():
                continue
            email = c.business_email.strip() if c.business_email else None
            phone = c.business_phone.strip() if c.business_phone else None
            # Never invent — if absent, stay None
            domain_match = False
            if email and self.EMAIL_RE.match(email):
                email_domain = email.split("@", 1)[1].lower()
                domain_match = bool(domain) and (email_domain == domain or email_domain.endswith("." + domain))
            elif email:
                email = None  # invalid format discarded, not rewritten
            if phone and not self.PHONE_RE.match(phone):
                phone = None
            role_valid = bool(c.role and any(a in c.role.lower() for a, _ in ROLE_ALIASES))
            public_presence = bool(c.linkedin_url or c.company_profile_url)
            conflicts: list[str] = []
            if c.business_email and email is None:
                conflicts.append("invalid_email_format")
            if c.business_phone and phone is None:
                conflicts.append("invalid_phone_format")
            freshness = 80.0 if (c.observed_at and (now - c.observed_at).total_seconds() < 86400 * 30) else 50.0
            conf = 30.0
            if email:
                conf += 25.0
            if domain_match:
                conf += 20.0
            if role_valid:
                conf += 10.0
            if public_presence:
                conf += 10.0
            if phone:
                conf += 5.0
            accepted = conf >= 55.0 and bool(c.full_name) and (email is not None or public_presence)
            country_code = None
            if phone and phone.startswith("+"):
                digits = re.match(r"\+(\d{1,3})", phone)
                country_code = digits.group(1) if digits else None
            results.append(
                ContactValidationResult(
                    full_name=c.full_name.strip(),
                    business_email=email,
                    domain_match=domain_match,
                    mx_check="interface_optional",
                    role_valid=role_valid,
                    public_presence=public_presence,
                    business_phone=phone,
                    country_code=country_code,
                    verification="verified" if accepted and domain_match else ("observed" if accepted else "rejected"),
                    freshness=freshness,
                    conflicts=conflicts,
                    confidence=min(95.0, conf),
                    source=c.source,
                    last_verified=c.observed_at or now,
                    evidence=[f"accepted:{accepted}", "never_invent:true", f"source:{c.source}"],
                    accepted=accepted,
                )
            )
        return results


class ContactDiscoveryEngine:
    """Pass-through discovery — only returns observed contacts, never fabricates."""

    def discover(self, item: AccountIntelligenceInput) -> list[ObservedContact]:
        return [c for c in item.observed_contacts if c.full_name.strip()]
