from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from production_hardening.models.types import DuplicateMergePlan


class DuplicateResolutionEngine:
    """Merge companies by domain / website / LinkedIn / aliases / legal name."""

    def canonical_key(self, payload: dict[str, Any]) -> str | None:
        domain = self._domain(payload.get("domain") or payload.get("primary_domain") or payload.get("website"))
        if domain:
            return f"domain:{domain}"
        linkedin = str(payload.get("linkedin_url") or payload.get("linkedin_company_url") or "").strip().lower()
        if linkedin:
            return f"linkedin:{linkedin.rstrip('/')}"
        legal = str(payload.get("legal_name") or "").strip().lower()
        if legal:
            return f"legal:{legal}"
        alias = str(payload.get("normalized_name") or payload.get("company_name") or "").strip().lower()
        if alias:
            return f"name:{alias}"
        return None

    def plan_merges(self, companies: list[dict[str, Any]]) -> list[DuplicateMergePlan]:
        buckets: dict[str, list[dict[str, Any]]] = {}
        for company in companies:
            key = self.canonical_key(company)
            if not key:
                continue
            buckets.setdefault(key, []).append(company)

        plans: list[DuplicateMergePlan] = []
        for key, group in buckets.items():
            if len(group) < 2:
                continue
            # Prefer company with domain + highest signal_frequency / earliest created
            ranked = sorted(
                group,
                key=lambda c: (
                    0 if c.get("primary_domain") or c.get("domain") else 1,
                    -int(c.get("signal_frequency") or 0),
                    str(c.get("created_at") or ""),
                ),
            )
            canonical = ranked[0]
            merged = [str(c.get("id") or c.get("company_id")) for c in ranked[1:]]
            plans.append(
                DuplicateMergePlan(
                    canonical_company_id=str(canonical.get("id") or canonical.get("company_id")),
                    merged_company_ids=merged,
                    match_keys=[key],
                    evidence=[f"group_size:{len(group)}", f"key:{key}"],
                )
            )
        return plans

    def _domain(self, value: Any) -> str | None:
        if not value:
            return None
        raw = str(value).strip().lower()
        if "://" not in raw:
            raw = f"https://{raw}"
        host = urlparse(raw).hostname or str(value).strip().lower()
        host = host.removeprefix("www.")
        return host or None
