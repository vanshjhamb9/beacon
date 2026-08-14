"""Canonical identity — one name, one official website, one domain."""

from __future__ import annotations

from typing import Any

from entity_resolution.models.types import (
    UNKNOWN,
    CanonicalIdentity,
    DomainValidation,
    EntityCandidate,
    IdentityScore,
    OfficialWebsite,
)


class CanonicalIdentityEngine:
    def build(
        self,
        entity: EntityCandidate,
        website: OfficialWebsite,
        validation: DomainValidation,
        score: IdentityScore,
        *,
        payload: dict[str, Any] | None = None,
    ) -> CanonicalIdentity:
        payload = payload or {}
        if not website.discovered:
            return CanonicalIdentity(company_name=entity.name, confidence=score.score, evidence=["no_website"])
        return CanonicalIdentity(
            company_name=entity.name if entity.name != UNKNOWN else UNKNOWN,
            official_website=website.website,
            domain=website.domain,
            logo_url=validation.favicon_url or payload.get("logo_url"),
            industry=payload.get("industry") or (payload.get("metadata") or {}).get("industry") or ("Software" if payload.get("source") == "product_hunt" else None),
            country=payload.get("country") or (payload.get("metadata") or {}).get("country"),
            linkedin_url=payload.get("linkedin_url") or (payload.get("metadata") or {}).get("linkedin_company"),
            description=(
                payload.get("description")
                or payload.get("body")
                or payload.get("content")
                or payload.get("title")
            ),
            confidence=score.score,
            evidence=[
                f"domain:{website.domain}",
                f"source:{website.source}",
                f"confidence:{score.score}",
                *entity.evidence[:3],
            ],
        )
