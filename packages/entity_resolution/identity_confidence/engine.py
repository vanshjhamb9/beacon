"""Identity confidence — only 90+ creates a company."""

from __future__ import annotations

from typing import Any

from entity_resolution.models.types import DomainValidation, EntityCandidate, IdentityScore, OfficialWebsite, UNKNOWN
from intelligence.entity_resolution.normalization import normalize_company_name

IDENTITY_THRESHOLD = 90.0


class ErowdIdentityConfidenceEngine:
    """Website +40, HTTPS +10, name match +20, LinkedIn +10, favicon/title +10, industry +10."""

    def score(
        self,
        entity: EntityCandidate,
        website: OfficialWebsite,
        validation: DomainValidation,
        *,
        payload: dict[str, Any] | None = None,
    ) -> IdentityScore:
        payload = payload or {}
        evidence: list[str] = []

        website_pts = 40.0 if website.discovered and website.domain else 0.0
        if website_pts:
            evidence.append("website_discovered:+40")

        https_pts = 10.0 if validation.https or (website.website or "").startswith("https://") else 0.0
        if https_pts:
            evidence.append("https:+10")

        name_pts = 0.0
        if entity.name != UNKNOWN and website.domain:
            token = normalize_company_name(entity.name).replace(" ", "")
            host = website.domain.split(".")[0].replace("-", "")
            if token and host and (token in host or host in token or any(normalize_company_name(a).replace(" ", "") in host for a in entity.aliases)):
                name_pts = 20.0
                evidence.append("name_match:+20")
            elif website.source.startswith("product_hunt") and website.discovered:
                # PH product name paired with discovered official site
                name_pts = 20.0
                evidence.append("ph_name_site_pair:+20")

        linkedin_pts = 10.0 if payload.get("linkedin_url") or payload.get("linkedin_company") or (payload.get("metadata") or {}).get("linkedin_website") else 0.0
        if linkedin_pts:
            evidence.append("linkedin:+10")

        favicon_title = 0.0
        if validation.title or validation.favicon_url or payload.get("website_title"):
            favicon_title = 10.0
            evidence.append("favicon_title:+10")
        elif validation.verified:
            favicon_title = 10.0
            evidence.append("verified_site:+10")

        industry_pts = 10.0 if payload.get("industry") or (payload.get("metadata") or {}).get("industry") else 0.0
        if not industry_pts and payload.get("source") == "product_hunt" and website.discovered:
            industry_pts = 10.0
            evidence.append("ph_software_default:+10")
        elif industry_pts:
            evidence.append("industry:+10")

        total = round(website_pts + https_pts + name_pts + linkedin_pts + favicon_title + industry_pts, 2)
        return IdentityScore(
            score=total,
            website_discovered=website_pts,
            https=https_pts,
            name_match=name_pts,
            linkedin_match=linkedin_pts,
            favicon_title=favicon_title,
            industry=industry_pts,
            passed=total >= IDENTITY_THRESHOLD and website.discovered and validation.verified,
            threshold=IDENTITY_THRESHOLD,
            evidence=evidence + [f"score:{total}"],
        )
