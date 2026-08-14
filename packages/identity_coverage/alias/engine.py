"""Alias resolution — merge name/domain variants into one canonical node."""

from __future__ import annotations

import re
from typing import Any

from identity_coverage.models.types import AliasNode


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


class AliasResolutionEngine:
    def resolve(self, payload: dict[str, Any], *, domain: str | None = None) -> AliasNode:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        names: list[str] = []
        for key in ("trade_name", "name", "title", "company_name"):
            v = payload.get(key)
            if v:
                names.append(str(v).strip())
        for h in meta.get("company_hints") or []:
            if h:
                names.append(str(h).strip())
        if domain:
            names.append(domain.split(".")[0])

        cleaned = [n for n in names if n and n.lower() != "unknown"]
        primary = cleaned[0] if cleaned else "unknown"
        aliases: list[str] = []
        seen = {_norm(primary)}
        evidence = [f"primary:{primary}"]
        for n in cleaned[1:]:
            key = _norm(n)
            if not key or key in seen:
                continue
            # Accept as alias if same normalized root or contains primary root
            root = _norm(primary)
            if key == root or root in key or key in root or (domain and key == _norm(domain.split(".")[0])):
                aliases.append(n)
                seen.add(key)
                evidence.append(f"alias:{n}")

        conf = 70.0 + min(25.0, 5.0 * len(aliases))
        if domain:
            conf += 10.0
            evidence.append(f"domain:{domain}")
        return AliasNode(
            primary_name=primary,
            aliases=aliases,
            official_domain=domain,
            merge_evidence=evidence,
            confidence=min(99.0, conf),
            reason="normalized_alias_graph",
        )

    def same_company(self, a: AliasNode, b: AliasNode) -> bool:
        if a.official_domain and b.official_domain and a.official_domain == b.official_domain:
            return True
        if _norm(a.primary_name) == _norm(b.primary_name) and a.official_domain and a.official_domain == b.official_domain:
            return True
        return False
