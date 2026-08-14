"""Canonical merge — one company per official domain / normalized name+domain."""

from __future__ import annotations

import re
from typing import Any

from identity_graph.models.types import CanonicalCompany, MergeResult


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


class CanonicalMergeEngine:
    def merge(
        self,
        *,
        name: str,
        domain: str | None,
        existing: list[dict[str, Any]] | list[CanonicalCompany] | None = None,
    ) -> MergeResult:
        existing = existing or []
        n = _norm(name)
        d = (domain or "").lower().removeprefix("www.")

        for item in existing:
            if isinstance(item, CanonicalCompany):
                eid = item.id
                edomain = (item.official_domain or "").lower()
                ename = _norm(item.trade_name or item.legal_name)
                aliases = [_norm(a) for a in item.aliases]
            else:
                eid = item.get("id") or item.get("canonical_id")
                edomain = str(item.get("official_domain") or item.get("domain") or "").lower()
                ename = _norm(str(item.get("trade_name") or item.get("legal_name") or item.get("name") or ""))
                aliases = [_norm(str(a)) for a in (item.get("aliases") or [])]

            matched: list[str] = []
            if d and edomain and d == edomain:
                matched.append("official_domain")
            if n and ename and n == ename and d and edomain and d == edomain:
                matched.append("name+domain")
            if n and n in aliases and d and edomain and d == edomain:
                matched.append("alias+domain")
            if matched:
                return MergeResult(
                    canonical_id=str(eid) if eid else None,
                    merged=True,
                    matched_on=matched,
                    evidence=[f"merge:{m}" for m in matched],
                )

        return MergeResult(merged=False, evidence=["no_existing_match"])
