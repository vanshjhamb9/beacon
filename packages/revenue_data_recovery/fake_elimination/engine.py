from __future__ import annotations

import re
from typing import Any

from production_hardening.admission.engine import FAKE_NAME_PATTERNS, OpportunityAdmissionGate
from revenue_data_recovery.models.types import FakeEliminationResult, UNKNOWN

NON_BUSINESS_ENTITY_TYPES = frozenset(
    {
        "repository",
        "project",
        "library",
        "package",
        "tool",
        "framework",
        "news",
        "blog",
        "blog_post",
        "reddit_user",
        "hn_user",
        "rss_title",
        "documentation",
        "open_source",
        "tutorial",
        "community",
        "discord",
        "slack",
        "github_org",
        "individual",
        "username",
    }
)

NON_BUSINESS_NAME_HINTS = (
    "readme",
    "awesome-",
    "tutorial",
    "how to",
    "getting started",
    "discord",
    "slack community",
    "open source",
    "npm package",
    "pypi",
    "crates.io",
    "vs code extension",
)

BUSINESS_CATEGORIES = frozenset(
    {
        "registered business",
        "startup",
        "saas",
        "agency",
        "manufacturing",
        "healthcare",
        "finance",
        "retail",
        "automotive",
        "construction",
        "enterprise",
        "smb",
        "software",
        "services",
        "b2b",
        "b2c",
    }
)

GITHUB_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")


class FakeCompanyEliminationEngine:
    """Reject non-business entities. Keep only real businesses."""

    def __init__(self) -> None:
        self._admission = OpportunityAdmissionGate()

    def evaluate(self, payload: dict[str, Any]) -> FakeEliminationResult:
        name = str(payload.get("company_name") or payload.get("name") or payload.get("legal_name") or "").strip()
        entity_type = str(payload.get("entity_type") or "").strip().lower() or UNKNOWN
        reasons: list[str] = []
        evidence: list[str] = []

        if not name:
            reasons.append("missing_name")
        else:
            lower = name.lower()
            if lower in FAKE_NAME_PATTERNS:
                reasons.append("fake_name_pattern")
            if any(h in lower for h in NON_BUSINESS_NAME_HINTS):
                reasons.append("non_business_name_hint")
            if GITHUB_USER_RE.match(name) and str(payload.get("source") or "").lower().startswith("github"):
                reasons.append("github_username")
            evidence.append(f"name:{name}")

        if entity_type in NON_BUSINESS_ENTITY_TYPES:
            reasons.append(f"rejected_entity_type:{entity_type}")

        url = str(payload.get("url") or payload.get("source_url") or "")
        if "/blob/" in url or "/pull/" in url or "/issues/" in url:
            reasons.append("repository_url")
        if "reddit.com/user/" in url.lower() or "news.ycombinator.com/user" in url.lower():
            reasons.append("social_username_url")

        # Compose with PH admission for domain/platform checks
        admission = self._admission.evaluate(payload)
        for reason in admission.reasons:
            if reason not in reasons:
                # Map admission reasons that indicate fakeness
                if reason in {
                    "fake_or_platform_label",
                    "github_username_or_individual",
                    "platform_domain_not_company",
                    "non_business_content",
                } or reason.startswith("rejected_entity_type:"):
                    reasons.append(reason)

        category = str(payload.get("business_category") or payload.get("category") or "").lower()
        industry = str(payload.get("industry") or "").lower()
        is_business_hint = category in BUSINESS_CATEGORIES or any(
            c in industry for c in ("saas", "health", "financ", "retail", "manufactur", "agency", "enterprise")
        )

        is_fake = len(reasons) > 0
        # Explicit business signals can override weak RSS-title-only noise only when admission passes name+domain
        if is_fake and is_business_hint and "fake_name_pattern" not in reasons and "github_username" not in reasons:
            soft = {r for r in reasons if r.startswith("rejected_entity_type:") or r == "non_business_name_hint"}
            if reasons and set(reasons) <= soft and admission.verdict.value == "ADMIT":
                reasons = []
                is_fake = False
                evidence.append("business_category_override")

        is_business = (not is_fake) and bool(name) and (
            is_business_hint
            or bool(payload.get("website") or payload.get("domain") or payload.get("primary_domain"))
        )
        if is_business:
            evidence.append("business:true")
        if is_fake:
            evidence.append("fake:true")

        return FakeEliminationResult(
            is_fake=is_fake,
            is_business=is_business and not is_fake,
            reasons=reasons,
            entity_type=entity_type,
            evidence=evidence or ["evaluated"],
        )
