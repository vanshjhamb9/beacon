from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from production_hardening.admission.engine import FAKE_NAME_PATTERNS
from revenue_quality_recovery.models.types import AttributedField, IdentityValidationResult, UNKNOWN

REJECT_ENTITY_TYPES = frozenset(
    {
        "repository",
        "reddit_user",
        "blog",
        "forum",
        "template",
        "open_source",
        "opensource",
        "fake_startup",
        "personal_portfolio",
        "portfolio",
        "library",
        "framework",
        "documentation",
        "community",
    }
)

REJECT_URL_HINTS = (
    "github.com/",
    "reddit.com/user/",
    "reddit.com/r/",
    "medium.com/",
    "dev.to/",
    "wordpress.com/",
    "blogspot.",
    "notion.site",
    "github.io",
)

IDENTITY_CHECKS = (
    "website_alive",
    "dns",
    "ssl",
    "favicon",
    "title",
    "logo",
    "organization_schema",
    "legal_name",
    "linkedin_exists",
    "domain_age",
)


class IdentityValidatorEngine:
    """Rule 4 — validate identity before company creation; reject non-business entities."""

    def validate(self, payload: dict[str, Any]) -> IdentityValidationResult:
        name = str(payload.get("legal_name") or payload.get("company_name") or payload.get("name") or "").strip()
        entity_type = str(payload.get("entity_type") or "").lower()
        url = str(payload.get("url") or payload.get("source_url") or payload.get("website") or "")
        reasons: list[str] = []
        evidence: list[str] = []
        checks: dict[str, bool] = {}

        if not name:
            reasons.append("missing_legal_name")
        elif name.lower() in FAKE_NAME_PATTERNS:
            reasons.append("fake_startup_name")
        elif entity_type in REJECT_ENTITY_TYPES:
            reasons.append(f"rejected_entity_type:{entity_type}")
        if any(h in url.lower() for h in REJECT_URL_HINTS):
            reasons.append("non_business_url")
        if entity_type in {"repository", "open_source", "opensource"} or "/blob/" in url or "/tree/" in url:
            reasons.append("github_repository_or_opensource")
        if entity_type in {"reddit_user", "hn_user"} or "reddit.com/user/" in url.lower():
            reasons.append("reddit_or_forum_user")
        if entity_type in {"blog", "personal_portfolio", "portfolio"}:
            reasons.append("blog_or_portfolio")
        if entity_type == "template" or "template" in name.lower():
            reasons.append("template_site")

        # Positive identity checks from observed signals only — never invent DNS/SSL
        checks["website_alive"] = bool(payload.get("website_alive") or payload.get("http_status") in (200, "200") or payload.get("website_verified"))
        checks["dns"] = bool(payload.get("dns_ok") or payload.get("dns") or checks["website_alive"])
        checks["ssl"] = bool(payload.get("ssl") or payload.get("https"))
        checks["favicon"] = bool(payload.get("favicon") or payload.get("favicon_url") or payload.get("favicon_hash"))
        checks["title"] = bool(payload.get("website_title") or payload.get("title") or (payload.get("open_graph") or {}).get("title"))
        checks["logo"] = bool(payload.get("logo") or payload.get("logo_url") or (payload.get("open_graph") or {}).get("image"))
        schema = payload.get("organization_schema") or payload.get("schema_org") or {}
        checks["organization_schema"] = bool(schema) and (
            str(schema.get("@type") or schema.get("type") or "").lower() in {"organization", "corporation", "localbusiness", ""}
            or "name" in schema
        )
        checks["legal_name"] = bool(name) and name.lower() not in FAKE_NAME_PATTERNS
        linkedin = payload.get("linkedin_company") or payload.get("linkedin_company_url") or payload.get("linkedin_url")
        checks["linkedin_exists"] = bool(linkedin) and "linkedin.com" in str(linkedin).lower()
        checks["domain_age"] = bool(payload.get("domain_age_days") or payload.get("domain_age") or payload.get("whois_created"))

        passed = sum(1 for v in checks.values() if v)
        confidence = round(100.0 * passed / len(IDENTITY_CHECKS), 2)

        # Accept only if no rejection reasons AND core checks
        core_ok = checks["legal_name"] and (checks["website_alive"] or checks["dns"] or bool(payload.get("website") or payload.get("domain")))
        rejected = len(reasons) > 0
        accepted = (not rejected) and core_ok and passed >= 4

        if accepted:
            evidence.append("identity:accepted")
        else:
            evidence.append("identity:rejected" if rejected or not accepted else "identity:incomplete")
            if not accepted and not reasons:
                reasons.append("insufficient_identity_checks")

        legal = AttributedField.of(
            name or None,
            source=str(payload.get("source") or "identity_validator"),
            collected_at=payload.get("collected_at"),
            confidence=confidence if name else None,
            verification="validated" if accepted else "rejected",
            evidence=["legal_name_check"],
        )

        # Domain normalization evidence
        domain = payload.get("domain") or self._host(payload.get("website"))
        if domain:
            evidence.append(f"domain:{domain}")

        return IdentityValidationResult(
            accepted=accepted,
            rejected=rejected or not accepted,
            rejection_reasons=reasons if (rejected or not accepted) else [],
            checks=checks,
            legal_name=legal,
            linkedin_exists=checks["linkedin_exists"],
            confidence=confidence,
            evidence=evidence + [f"checks_passed:{passed}/{len(IDENTITY_CHECKS)}"],
        )

    def _host(self, value: Any) -> str | None:
        if not value:
            return None
        raw = str(value)
        if "://" not in raw:
            raw = f"https://{raw}"
        try:
            return (urlparse(raw).hostname or "").removeprefix("www.") or None
        except Exception:  # noqa: BLE001
            return None
