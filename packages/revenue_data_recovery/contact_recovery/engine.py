from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import AttributedValue, ContactRecoveryResult, RecoveredContact, UNKNOWN

TARGET_ROLES = (
    "Founder",
    "CEO",
    "CTO",
    "COO",
    "VP Engineering",
    "Innovation",
    "Sales",
    "Operations",
    "Support",
    "Marketing",
    "Business Development",
    "Product",
)

ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "Founder": ("founder", "co-founder", "cofounder", "owner"),
    "CEO": ("ceo", "chief executive", "chief executive officer"),
    "CTO": ("cto", "chief technology", "chief technical"),
    "COO": ("coo", "chief operating"),
    "VP Engineering": ("vp engineering", "vp of engineering", "head of engineering", "engineering director"),
    "Innovation": ("innovation", "head of innovation", "chief innovation"),
    "Sales": ("sales", "vp sales", "head of sales", "chief revenue", "cro"),
    "Operations": ("operations", "vp operations", "head of operations"),
    "Support": ("support", "customer success", "customer support", "head of support"),
    "Marketing": ("marketing", "cmo", "vp marketing", "head of marketing"),
    "Business Development": ("business development", "bizdev", "bd ", "partnerships"),
    "Product": ("product", "cpo", "vp product", "head of product"),
}


class ContactRecoveryEngine:
    """Recover public contacts only — never fabricate names, emails, or phones."""

    def recover(self, payload: dict[str, Any]) -> ContactRecoveryResult:
        raw_people = list(payload.get("decision_makers") or []) + list(payload.get("contacts") or [])
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        evidence: list[str] = []
        by_role: dict[str, RecoveredContact] = {}

        for person in raw_people:
            if not isinstance(person, dict):
                continue
            name = str(person.get("name") or "").strip()
            if not name or name == UNKNOWN:
                evidence.append("skipped_nameless_contact")
                continue
            role_raw = str(person.get("role") or person.get("title") or "").strip()
            role = self._normalize_role(role_raw) or role_raw or UNKNOWN
            source = str(person.get("source") or payload.get("source") or "public_profile")
            conf = float(person.get("confidence") or 0.0)
            if conf and conf <= 1.0:
                conf *= 100.0

            email_val = person.get("email") or person.get("work_email")
            phone_val = person.get("phone") or person.get("business_phone")
            linkedin_val = person.get("linkedin") or person.get("linkedin_url")
            profile_val = person.get("public_profile") or person.get("source_url") or linkedin_val

            # Never invent channels — only attribute observed values
            contact = RecoveredContact(
                name=name,
                role=role,
                email=AttributedValue.of(
                    email_val,
                    source=source,
                    collected_at=collected_at,
                    confidence=conf or (85.0 if email_val else None),
                    evidence=["email_observed"] if email_val else ["email_missing"],
                ),
                phone=AttributedValue.of(
                    phone_val,
                    source=source,
                    collected_at=collected_at,
                    confidence=conf or (80.0 if phone_val else None),
                    evidence=["phone_observed"] if phone_val else ["phone_missing"],
                ),
                linkedin=AttributedValue.of(
                    linkedin_val,
                    source=source,
                    collected_at=collected_at,
                    confidence=conf or (80.0 if linkedin_val else None),
                    evidence=["linkedin_observed"] if linkedin_val else ["linkedin_missing"],
                ),
                public_profile=AttributedValue.of(
                    profile_val,
                    source=source,
                    collected_at=collected_at,
                    confidence=conf or (70.0 if profile_val else None),
                    evidence=["profile_observed"] if profile_val else ["profile_missing"],
                ),
                source=source,
                confidence=conf or (60.0 if name else 0.0),
                last_verified=person.get("last_verified") or collected_at,
                evidence=[f"contact:{name}:{role}", f"source:{source}"],
            )
            # Prefer higher confidence per canonical role
            key = role if role in ROLE_ALIASES else f"other:{name.lower()}"
            existing = by_role.get(key)
            if existing is None or contact.confidence > existing.confidence:
                by_role[key] = contact
                evidence.append(f"recovered:{role}:{name}")

        # Also harvest company-level emails/phones without inventing people
        for email in payload.get("emails") or []:
            if not email:
                continue
            evidence.append(f"company_email:{email}")
        for phone in payload.get("phones") or []:
            if not phone:
                continue
            evidence.append(f"company_phone:{phone}")

        contacts = list(by_role.values())
        role_hits = sum(1 for r in TARGET_ROLES if any(c.role == r for c in contacts))
        coverage = round(100.0 * role_hits / len(TARGET_ROLES), 2)
        email_count = sum(1 for c in contacts if c.email.value != UNKNOWN)
        phone_count = sum(1 for c in contacts if c.phone.value != UNKNOWN)
        dm_count = sum(1 for c in contacts if c.role in {"Founder", "CEO", "CTO", "COO", "VP Engineering"})

        return ContactRecoveryResult(
            contacts=contacts,
            coverage_percent=coverage,
            verified_email_count=email_count + sum(1 for e in (payload.get("emails") or []) if e),
            verified_phone_count=phone_count + sum(1 for p in (payload.get("phones") or []) if p),
            verified_decision_maker_count=dm_count,
            evidence=evidence or ["no_public_contacts"],
        )

    def _normalize_role(self, role: str) -> str | None:
        lower = role.lower()
        for canonical, aliases in ROLE_ALIASES.items():
            if lower == canonical.lower() or any(a in lower for a in aliases):
                return canonical
        return None
