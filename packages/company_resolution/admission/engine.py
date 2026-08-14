"""Phase 7–8 — admission gate. Only create company when all checks pass."""

from __future__ import annotations

from company_resolution.models.types import (
    CreAdmission,
    CreVerdict,
    IdentityConfidence,
    OrganizationCandidate,
    RawSignalEnvelope,
    RejectionReason,
    SourceAttribution,
    WebsiteValidation,
)

# Collectors that must NOT create companies from weak title extraction
SIGNAL_ONLY_SOURCES = frozenset(
    {
        "reddit",
        "hacker_news",
        "hn",
        "rss",
        "devto",
        "github_trending",
        "indie_hackers",
        "sec_edgar",
    }
)

# Product Hunt may create companies when identity already exists (name+domain)
PRODUCT_IDENTITY_SOURCES = frozenset({"product_hunt"})


class CreAdmissionEngine:
    def evaluate(
        self,
        signal: RawSignalEnvelope,
        *,
        org: OrganizationCandidate,
        identity: IdentityConfidence,
        website: WebsiteValidation,
        attribution: SourceAttribution,
    ) -> CreAdmission:
        reasons: list[RejectionReason] = []

        if not org.found:
            reasons.append(RejectionReason.NO_ORGANIZATION)
        if not org.official_domain and not org.linkedin_company:
            reasons.append(RejectionReason.NO_DOMAIN)
        if not identity.passed:
            reasons.append(RejectionReason.LOW_IDENTITY_CONFIDENCE)
        if not website.valid:
            reasons.append(website.reject_reason or RejectionReason.WEBSITE_INVALID)
        if not attribution.complete and not attribution.source_url:
            reasons.append(RejectionReason.MISSING_ATTRIBUTION)

        source = (signal.source or "").lower()
        # Signal-only sources: still allowed IF org+identity+website all pass (real domain found)
        # but reject when they only have platform URL / title token
        if source in SIGNAL_ONLY_SOURCES and not (org.official_domain and identity.passed and website.valid):
            reasons.append(RejectionReason.SOURCE_POLICY)

        # Deduplicate reasons
        seen: set[RejectionReason] = set()
        unique: list[RejectionReason] = []
        for r in reasons:
            if r in seen:
                continue
            seen.add(r)
            unique.append(r)

        admitted = len(unique) == 0 and org.found and identity.passed and website.valid
        # Product Hunt: require domain + identity; website may be assumed if domain present
        if not admitted and source in PRODUCT_IDENTITY_SOURCES:
            if org.found and org.official_domain and identity.passed and website.valid:
                admitted = True
                unique = []

        verdict = CreVerdict.ADMITTED if admitted else CreVerdict.REJECTED
        explanation = " → ".join(r.value for r in unique) if unique else "Admitted"
        return CreAdmission(
            admitted=admitted,
            verdict=verdict,
            reasons=unique,
            explanation=explanation,
            allow_create_company=admitted,
            evidence=[f"admitted:{admitted}", f"source:{source}", explanation],
        )
