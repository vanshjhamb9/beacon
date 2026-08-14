"""Phase 3 — Identity confidence. Reject below 90."""

from __future__ import annotations

from typing import Any

from company_resolution.models.types import IdentityConfidence, OrganizationCandidate, RawSignalEnvelope, UNKNOWN
from intelligence.entity_resolution.normalization import normalize_company_name
from intelligence.entity_resolution.platform_domains import is_platform_domain

IDENTITY_THRESHOLD = 90.0


class IdentityConfidenceEngine:
    def score(
        self,
        signal: RawSignalEnvelope,
        org: OrganizationCandidate,
        *,
        industry: str | None = None,
        description: str | None = None,
        country: str | None = None,
        website_valid: bool = False,
        extras: dict[str, Any] | None = None,
    ) -> IdentityConfidence:
        extras = extras or {}
        evidence: list[str] = []

        legal = 0.0
        if org.legal_name and org.legal_name != UNKNOWN:
            legal = 18.0
            evidence.append("legal_name")
            if len(org.legal_name.split()) >= 2:
                legal = 22.0

        domain_s = 0.0
        if org.official_domain and not is_platform_domain(org.official_domain):
            domain_s = 22.0
            evidence.append("official_domain")

        website_s = 0.0
        if website_valid or org.homepage:
            website_s = 15.0 if website_valid else 8.0
            evidence.append("website")

        industry_s = 8.0 if industry else (5.0 if signal.source == "product_hunt" else 0.0)
        if industry_s:
            evidence.append("industry")

        desc = description or (signal.body[:200] if signal.body else "") or (signal.title if signal.source == "product_hunt" else "")
        description_s = 10.0 if desc and len(desc) >= 40 else (5.0 if desc else 0.0)
        if description_s:
            evidence.append("description")

        country_s = 5.0 if country else 0.0
        if country_s:
            evidence.append("country")

        linkedin_s = 10.0 if org.linkedin_company else 0.0
        if linkedin_s:
            evidence.append("linkedin")

        # Consistency: name token appears in domain
        consistency = 0.0
        if org.legal_name and org.official_domain and org.legal_name != UNKNOWN:
            token = normalize_company_name(org.legal_name).replace(" ", "")[:8]
            host = org.official_domain.split(".")[0].replace("-", "")
            if token and host and (token in host or host in token):
                consistency = 13.0
                evidence.append("name_domain_consistent")
            elif signal.source == "product_hunt" and org.official_domain:
                consistency = 8.0
                evidence.append("product_hunt_domain_present")
        elif org.linkedin_company and org.legal_name != UNKNOWN:
            consistency = 8.0
            evidence.append("linkedin_name_pair")

        # Product Hunt boost when domain + name exist
        if signal.source == "product_hunt" and domain_s and legal:
            legal = max(legal, 22.0)
            domain_s = max(domain_s, 22.0)
            industry_s = max(industry_s, 8.0)
            description_s = max(description_s, 10.0)
            if consistency < 13.0:
                consistency = 13.0
                evidence.append("product_hunt_identity_boost")

        total = round(
            min(
                100.0,
                legal + domain_s + website_s + industry_s + description_s + country_s + linkedin_s + consistency,
            ),
            2,
        )
        # Cap without domain
        if not org.official_domain:
            total = min(total, 70.0)

        return IdentityConfidence(
            score=total,
            legal_name_score=legal,
            domain_score=domain_s,
            website_score=website_s,
            industry_score=industry_s,
            description_score=description_s,
            country_score=country_s,
            linkedin_score=linkedin_s,
            consistency_score=consistency,
            passed=total >= IDENTITY_THRESHOLD,
            threshold=IDENTITY_THRESHOLD,
            evidence=evidence + [f"score:{total}"],
        )
