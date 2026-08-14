from __future__ import annotations

import re

from lead_enrichment.models.types import (
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    PersonEntry,
    WebsiteFetchResult,
)

_ROLE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\b(founder|co[- ]founder)\b", "Founder", "Leadership"),
    (r"\bchief executive officer\b|\bceo\b", "CEO", "Leadership"),
    (r"\bchief technology officer\b|\bcto\b", "CTO", "Engineering"),
    (r"\bchief operating officer\b|\bcoo\b", "COO", "Operations"),
    (r"\bhead of support\b|\bsupport (director|lead|head)\b", "Head of Support", "Support"),
    (r"\bhead of operations\b|\boperations (director|lead|head)\b", "Head of Operations", "Operations"),
    (r"\bengineering manager\b|\bhead of engineering\b", "Engineering Manager", "Engineering"),
    (r"\bhead of marketing\b|\bmarketing (director|lead|head)\b|\bcmo\b", "Marketing Head", "Marketing"),
)

_NAME_ROLE_RE = re.compile(
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\s*[,|\-|–|—|:]\s*([A-Za-z][A-Za-z /&]{2,40})",
)


class PeopleExtractor:
    def extract(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None,
    ) -> list[PersonEntry]:
        people: list[PersonEntry] = []
        seen: set[str] = set()

        for known in item.known_people:
            name = str(known.get("name") or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            role = str(known.get("title") or known.get("role") or "Team Member")
            people.append(
                PersonEntry(
                    name=name,
                    role=role,
                    department=str(known.get("department") or self._department_for_role(role)),
                    linkedin_url=known.get("linkedin_url") if isinstance(known.get("linkedin_url"), str) else None,
                    work_email=known.get("email") if isinstance(known.get("email"), str) else None,
                    confidence=float(known.get("confidence") or 80.0),
                    source=EnrichmentSourceType.BEACON_INTELLIGENCE,
                )
            )

        if website:
            for page in website.pages:
                if page.page_type not in {"team", "about", "homepage"}:
                    continue
                for match in _NAME_ROLE_RE.finditer(page.text):
                    name, role_raw = match.group(1).strip(), match.group(2).strip()
                    role = self._normalize_role(role_raw)
                    if role is None:
                        continue
                    key = name.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    people.append(
                        PersonEntry(
                            name=name,
                            role=role,
                            department=self._department_for_role(role),
                            confidence=74.0 if page.page_type == "team" else 62.0,
                            source=EnrichmentSourceType.COMPANY_WEBSITE,
                            source_url=page.url,
                        )
                    )

        persona = str(item.revenue_recommendation.get("buyer_persona") or "").strip()
        if persona and not any(person.role.lower() == persona.lower() for person in people):
            people.append(
                PersonEntry(
                    name=f"{item.company_name} {persona}",
                    role=persona,
                    department=self._department_for_role(persona),
                    confidence=55.0,
                    source=EnrichmentSourceType.BEACON_REVENUE,
                )
            )
        return people

    def _normalize_role(self, role_raw: str) -> str | None:
        lowered = role_raw.lower()
        for pattern, label, _department in _ROLE_PATTERNS:
            if re.search(pattern, lowered, flags=re.I):
                return label
        return None

    def _department_for_role(self, role: str) -> str:
        lowered = role.lower()
        for pattern, _label, department in _ROLE_PATTERNS:
            if re.search(pattern, lowered, flags=re.I):
                return department
        if "support" in lowered:
            return "Support"
        if "market" in lowered:
            return "Marketing"
        if "engineer" in lowered or "cto" in lowered:
            return "Engineering"
        if "operat" in lowered or "coo" in lowered:
            return "Operations"
        return "Leadership"
