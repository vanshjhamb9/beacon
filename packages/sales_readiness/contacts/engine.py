from __future__ import annotations

from typing import Any

from sales_readiness.models.types import AttributedField, ContactCompleteness, RoleContact, UNKNOWN

ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "CEO": ("ceo", "chief executive", "founder & ceo"),
    "Founder": ("founder", "co-founder", "cofounder"),
    "CTO": ("cto", "chief technology", "vp engineering", "head of engineering"),
    "Sales": ("sales", "vp sales", "head of sales", "chief revenue", "cro", "sales director"),
    "Marketing": ("marketing", "cmo", "vp marketing", "head of marketing", "marketing director"),
    "Support": ("support", "head of support", "support manager", "customer success", "cx"),
    "Procurement": ("procurement", "purchasing", "vendor management"),
    "Operations": ("operations", "ops", "coo", "vp operations", "head of operations"),
    "Finance": ("finance", "cfo", "vp finance", "finance director", "controller"),
    "HR": ("hr", "chro", "vp people", "head of hr", "human resources"),
}


class ContactCompletenessEngine:
    """Measure role coverage from observed decision makers — never invent people."""

    def evaluate(self, payload: dict[str, Any]) -> ContactCompleteness:
        people = list(payload.get("decision_makers") or payload.get("people") or [])
        source_default = str(payload.get("source") or "decision_discovery")
        collected = payload.get("collected_at")
        roles_out: list[RoleContact] = []
        covered: set[str] = set()
        email_count = 0
        phone_count = 0
        evidence: list[str] = []

        for role in ROLE_ALIASES:
            match = self._find(role, people)
            if match is None:
                roles_out.append(RoleContact(role=role, evidence=[f"{role}:not_observed"]))
                continue
            covered.add(role)
            email = match.get("email") or match.get("work_email")
            phone = match.get("phone") or match.get("business_phone")
            linkedin = match.get("linkedin") or match.get("linkedin_url")
            profile = match.get("public_profile") or match.get("source_url")
            src = str(match.get("source") or source_default)
            conf = float(match.get("confidence") or 0.0)
            if email:
                email_count += 1
            if phone:
                phone_count += 1
            roles_out.append(
                RoleContact(
                    role=role,
                    name=str(match.get("name") or UNKNOWN),
                    verified_email=AttributedField.of(email, source=src, collected_at=collected, confidence=conf or 80.0, evidence=["email"] if email else []),
                    verified_phone=AttributedField.of(phone, source=src, collected_at=collected, confidence=conf or 70.0, evidence=["phone"] if phone else []),
                    linkedin=AttributedField.of(linkedin, source=src, collected_at=collected, confidence=conf or 75.0, evidence=["linkedin"] if linkedin else []),
                    public_profile=AttributedField.of(profile, source=src, collected_at=collected, confidence=conf or 60.0, evidence=["profile"] if profile else []),
                    confidence=conf,
                    evidence=[f"role:{role}", f"name:{match.get('name')}"],
                )
            )
            evidence.append(f"covered:{role}")

        coverage = round(len(covered) / max(len(ROLE_ALIASES), 1) * 100.0, 2)
        return ContactCompleteness(
            roles=roles_out,
            coverage_percent=coverage,
            verified_email_count=email_count,
            verified_phone_count=phone_count,
            evidence=evidence + [f"coverage:{coverage}"],
        )

    def _find(self, role: str, people: list[Any]) -> dict[str, Any] | None:
        aliases = ROLE_ALIASES[role]
        for person in people:
            if not isinstance(person, dict):
                continue
            title = str(person.get("title") or person.get("role") or person.get("normalized_role") or "").lower()
            if any(a in title for a in aliases):
                return person
        return None
