from __future__ import annotations

from typing import Any

from decision_discovery.extractors.roles import (
    department_for_role,
    is_plausible_person_name,
    normalize_role,
)
from decision_discovery.models.types import (
    DecisionMakerCandidate,
    DecisionRole,
    DiscoverySourceType,
    LeadershipEntry,
)


class DecisionMakerExtractor:
    """Extract named decision makers from verified public/enrichment evidence only."""

    def extract(self, people_rows: list[dict[str, Any]]) -> list[DecisionMakerCandidate]:
        candidates: list[DecisionMakerCandidate] = []
        seen: set[str] = set()

        for row in people_rows:
            name = str(row.get("name") or "").strip()
            role_raw = str(row.get("role") or row.get("title") or "").strip()
            if not name or not role_raw:
                continue
            tokens = name.split()
            if len(tokens) >= 2 and normalize_role(tokens[-1]) is not None:
                person_part = " ".join(tokens[:-1])
                if not is_plausible_person_name(person_part):
                    continue
                name = person_part
            if not is_plausible_person_name(name):
                continue

            normalized = normalize_role(role_raw)
            if normalized is None:
                continue
            role, department, seniority = normalized
            key = f"{name.lower()}::{role.value.lower()}"
            if key in seen:
                continue
            seen.add(key)

            email = row.get("work_email") or row.get("email")
            phone = row.get("business_phone")
            linkedin = row.get("linkedin_url")
            source = self._source(row.get("source"))
            source_url = row.get("source_url") if isinstance(row.get("source_url"), str) else None

            # Never keep personal contact fields unless explicitly marked public.
            is_public = bool(row.get("is_public", True))
            if not is_public:
                email = None
                phone = None

            if isinstance(email, str) and not self._looks_like_email(email):
                email = None
            if isinstance(phone, str) and not self._looks_like_phone(phone):
                phone = None
            if isinstance(linkedin, str) and "linkedin.com" not in linkedin.lower():
                linkedin = None

            confidence = float(row.get("confidence") or 70.0)
            candidates.append(
                DecisionMakerCandidate(
                    name=name,
                    role=role.value,
                    normalized_role=role,
                    department=str(row.get("department") or department),
                    seniority_rank=seniority,
                    work_email=email if isinstance(email, str) else None,
                    business_phone=phone if isinstance(phone, str) else None,
                    linkedin_url=linkedin if isinstance(linkedin, str) else None,
                    confidence=min(100.0, max(0.0, confidence)),
                    source=source,
                    source_url=source_url,
                    evidence=str(row.get("evidence") or f"Publicly attributed role '{role.value}' for {name}"),
                )
            )
        return candidates

    def to_leadership(self, makers: list[DecisionMakerCandidate]) -> list[LeadershipEntry]:
        leadership_roles = {
            DecisionRole.FOUNDER,
            DecisionRole.CEO,
            DecisionRole.CTO,
            DecisionRole.COO,
            DecisionRole.HEAD_OF_ENGINEERING,
            DecisionRole.HEAD_OF_OPERATIONS,
            DecisionRole.MARKETING_HEAD,
            DecisionRole.SALES_HEAD,
            DecisionRole.AI_LEAD,
        }
        return [
            LeadershipEntry(
                name=item.name,
                title=item.role,
                department=item.department or department_for_role(item.role),
                confidence=item.confidence,
                source=item.source,
                source_url=item.source_url,
                evidence=item.evidence,
            )
            for item in makers
            if item.normalized_role in leadership_roles
        ]

    def _source(self, value: object) -> DiscoverySourceType:
        if isinstance(value, DiscoverySourceType):
            return value
        if isinstance(value, str):
            try:
                return DiscoverySourceType(value)
            except ValueError:
                mapping = {
                    "company_website": DiscoverySourceType.COMPANY_WEBSITE,
                    "beacon_intelligence": DiscoverySourceType.BEACON_INTELLIGENCE,
                    "beacon_enrichment": DiscoverySourceType.BEACON_ENRICHMENT,
                    "linkedin": DiscoverySourceType.LINKEDIN_COMPANY,
                }
                return mapping.get(value, DiscoverySourceType.BEACON_ENRICHMENT)
        return DiscoverySourceType.BEACON_ENRICHMENT

    def _looks_like_email(self, value: str) -> bool:
        return "@" in value and "." in value.split("@")[-1] and " " not in value.strip()

    def _looks_like_phone(self, value: str) -> bool:
        digits = sum(char.isdigit() for char in value)
        return digits >= 7
