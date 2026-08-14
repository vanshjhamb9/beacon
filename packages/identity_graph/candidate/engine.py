"""Identity candidate extraction from signals — never creates companies."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from identity_graph.models.types import IdentityCandidate, SourceRole, UNKNOWN
from identity_graph.source_roles.engine import SourceRoleEngine
from intelligence.entity_resolution.platform_domains import is_platform_domain


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip())


class CandidateEngine:
    def __init__(self) -> None:
        self.roles = SourceRoleEngine()

    def extract(self, payload: dict[str, Any]) -> IdentityCandidate:
        source = str(payload.get("source") or UNKNOWN).lower()
        role = self.roles.role(source)
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        title = str(payload.get("title") or "")
        name = UNKNOWN
        aliases: list[str] = []

        hints = meta.get("company_hints") or payload.get("company_hints") or []
        if isinstance(hints, list) and hints:
            name = _normalize_name(str(hints[0]))
            aliases = [_normalize_name(str(h)) for h in hints[1:6] if str(h).strip()]

        if name in {"", UNKNOWN}:
            # GitHub: owner/repo → prefer owner or product slug when org-shaped
            if source == "github_trending" and "GitHub:" in title:
                slug = title.split("GitHub:", 1)[-1].strip()
                if "/" in slug:
                    owner, repo = slug.split("/", 1)
                    name = _normalize_name(repo.replace("-", " ").replace("_", " "))
                    aliases.append(owner)
            elif source == "product_hunt" and title:
                name = _normalize_name(title.split("—")[0].split("-")[0].strip())
            elif title:
                name = _normalize_name(title[:80])

        domain = None
        for key in ("official_domain", "domain", "possible_domain"):
            raw = meta.get(key) or payload.get(key)
            if not raw:
                continue
            host = str(raw).lower().removeprefix("www.")
            if host and not is_platform_domain(host) and "." in host:
                domain = host
                break
        for key in ("official_website", "homepage", "repo_homepage", "canonical_website"):
            raw = meta.get(key) or payload.get(key)
            if not raw:
                continue
            try:
                host = urlparse(str(raw) if "://" in str(raw) else f"https://{raw}").netloc.lower().removeprefix("www.")
            except ValueError:
                continue
            if host and not is_platform_domain(host):
                domain = host
                break

        confidence = 40.0
        evidence = [f"source:{source}", f"role:{role.value}"]
        if name not in {"", UNKNOWN}:
            confidence += 25.0
            evidence.append(f"name:{name}")
        if domain:
            confidence += 30.0
            evidence.append(f"domain:{domain}")
        if role == SourceRole.IDENTITY:
            confidence += 10.0
        if role == SourceRole.CONVERSATION:
            confidence = min(confidence, 55.0)

        return IdentityCandidate(
            name=name or UNKNOWN,
            aliases=list(dict.fromkeys([a for a in aliases if a and a.lower() != (name or "").lower()])),
            possible_domain=domain,
            source=source,
            confidence=min(99.0, confidence),
            evidence=evidence,
            signal_id=str(payload.get("signal_id") or payload.get("id") or UNKNOWN),
            source_role=role,
        )
