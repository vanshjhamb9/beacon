from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from intelligence.entity_resolution.platform_domains import is_platform_domain, is_platform_label
from production_hardening.models.types import AdmissionDecision, AdmissionVerdict

FAKE_NAME_PATTERNS = frozenset(
    {
        "mixture",
        "optimizing",
        "sensor",
        "investor",
        "monitor",
        "building",
        "engineering",
        "hardware",
        "software",
        "automation",
        "intelligence",
        "metacognition",
        "osint",
        "capa",
        "heavy",
        "touch",
        "basic",
        "natural",
        "nonprofit",
        "mobility",
        "according",
        "last",
        "can",
        "kodak",
        "suno",
        "orchid",
        "odyssey",
        "bananas",
        "claude",
        "qwen",
        "codex",
        "minecraft",
        "indieweb",
        "homeLab".lower(),
        "homelab",
        "orion",
        "jensen",
        "resolviendo",
        "spycost",
        "openseo",
        "detourmap",
        "rewisp",
        "basert",
        "kobbe",
        "web-accessibility",
        "kieran",
    }
)

NON_BUSINESS_HINTS = (
    "github.com/",
    "/blob/",
    "/pull/",
    "/issues/",
    "readme",
    "documentation",
    "docs.",
    "npmjs.com",
    "pypi.org",
    "crates.io",
    "arxiv.org",
    "stackoverflow.com",
    "medium.com/",
    "substack.com",
    "wikipedia.org",
)

GITHUB_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")


class OpportunityAdmissionGate:
    """Reject non-business / unverifiable identities before founder surfaces."""

    def evaluate(self, payload: dict[str, Any]) -> AdmissionDecision:
        name = str(payload.get("company_name") or payload.get("name") or "").strip()
        domain = self._normalize_domain(payload.get("domain") or payload.get("primary_domain") or payload.get("website"))
        source = str(payload.get("source") or "").strip()
        evidence = payload.get("evidence") or payload.get("evidence_ids") or []
        use_case = str(payload.get("use_case") or payload.get("business_use_case") or payload.get("narrative") or "").strip()
        reasons: list[str] = []
        proof: list[str] = []

        if not name:
            reasons.append("no_company_identity")
        elif is_platform_label(name) or name.lower() in FAKE_NAME_PATTERNS:
            reasons.append("fake_or_platform_label")
        elif self._looks_like_github_username(name, domain, source):
            reasons.append("github_username_or_individual")

        if not domain:
            reasons.append("no_website_or_domain")
        elif is_platform_domain(domain):
            reasons.append("platform_domain_not_company")
            proof.append(f"domain:{domain}")
        else:
            proof.append(f"domain:{domain}")

        if not source:
            reasons.append("no_source")
        else:
            proof.append(f"source:{source}")

        if not evidence:
            reasons.append("no_opportunity_evidence")
        else:
            proof.append(f"evidence_count:{len(evidence) if hasattr(evidence, '__len__') else 1}")

        if not use_case or len(use_case) < 20:
            reasons.append("no_business_use_case")

        url = str(payload.get("url") or "")
        if any(hint in url.lower() for hint in NON_BUSINESS_HINTS):
            reasons.append("non_business_content")

        entity_type = str(payload.get("entity_type") or "").lower()
        if entity_type in {"repository", "library", "framework", "individual", "community", "documentation", "news"}:
            reasons.append(f"rejected_entity_type:{entity_type}")

        verdict = AdmissionVerdict.REJECT if reasons else AdmissionVerdict.ADMIT
        if verdict == AdmissionVerdict.ADMIT:
            proof.append("admission:pass")
        return AdmissionDecision(
            verdict=verdict,
            reasons=reasons,
            evidence=proof,
            company_name=name or None,
            domain=domain,
        )

    def _normalize_domain(self, value: Any) -> str | None:
        if not value:
            return None
        raw = str(value).strip().lower()
        if "://" not in raw:
            raw = f"https://{raw}"
        try:
            host = urlparse(raw).hostname or ""
        except Exception:  # noqa: BLE001
            host = str(value).strip().lower()
        host = host.removeprefix("www.")
        if not host or "." not in host:
            # reject single-token "domains" like next.js package names without TLD structure
            if host and host.count(".") == 1 and not host.endswith((".com", ".io", ".ai", ".co", ".org", ".net", ".dev")):
                # allow .js style package false positives as reject via no real company domain
                if host.endswith((".js", ".ts", ".py", ".rb")):
                    return None
            if "." not in host:
                return None
        return host or None

    def _looks_like_github_username(self, name: str, domain: str | None, source: str) -> bool:
        if source in {"github_trending", "github"} and domain is None:
            return bool(GITHUB_USER_RE.match(name)) and " " not in name
        if "-" in name and " " not in name and domain is None and GITHUB_USER_RE.match(name):
            return True
        return False
