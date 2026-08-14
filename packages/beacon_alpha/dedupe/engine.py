from __future__ import annotations

import hashlib
import re
from typing import Any

from beacon_alpha.models.types import DedupeResult, UNKNOWN


class AlphaDedupeEngine:
    """Rule 8 — prevent duplicates via domain, LinkedIn, legal name, normalized name, website hash."""

    def fingerprint(self, payload: dict[str, Any]) -> dict[str, str]:
        domain = self._norm_domain(payload.get("domain") or payload.get("website") or payload.get("primary_domain"))
        linkedin = self._norm(payload.get("linkedin_company") or payload.get("linkedin_url") or payload.get("linkedin"))
        legal = self._norm(payload.get("legal_name") or payload.get("company_name") or payload.get("name"))
        normalized = self._normalize_company_name(payload.get("company_name") or payload.get("legal_name") or "")
        website_hash = str(payload.get("website_hash") or "")
        if not website_hash:
            site = self._norm(payload.get("website") or domain)
            website_hash = hashlib.sha1(site.encode("utf-8")).hexdigest()[:16] if site else ""
        return {
            "domain": domain,
            "linkedin": linkedin,
            "legal_name": legal,
            "normalized_name": normalized,
            "website_hash": website_hash,
        }

    def match(self, a: dict[str, Any], b: dict[str, Any]) -> DedupeResult:
        fa, fb = self.fingerprint(a), self.fingerprint(b)
        keys: list[str] = []
        for key in ("domain", "linkedin", "legal_name", "normalized_name", "website_hash"):
            if fa[key] and fa[key] == fb[key]:
                keys.append(key)
        is_dup = len(keys) >= 1 and (
            "domain" in keys or "linkedin" in keys or "website_hash" in keys or len(keys) >= 2
        )
        conf = min(99.0, 35.0 + 15.0 * len(keys)) if keys else 0.0
        return DedupeResult(
            is_duplicate=is_dup,
            match_keys=keys,
            canonical_company_id=str(a.get("company_id") or a.get("id") or "") or None,
            confidence=round(conf, 2),
            evidence=[f"match:{k}" for k in keys] or ["no_match"],
        )

    def filter_queue(self, companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep first occurrence; drop later duplicates."""
        kept: list[dict[str, Any]] = []
        for company in companies:
            dup = False
            for prior in kept:
                if self.match(prior, company).is_duplicate:
                    dup = True
                    break
            if not dup:
                kept.append(company)
        return kept

    def _norm(self, value: Any) -> str:
        if not value or value == UNKNOWN:
            return ""
        return str(value).strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.")

    def _norm_domain(self, value: Any) -> str:
        raw = self._norm(value)
        return raw.split("/")[0] if raw else ""

    def _normalize_company_name(self, name: Any) -> str:
        raw = self._norm(name)
        raw = re.sub(r"\b(inc|llc|ltd|corp|co|gmbh|plc)\b\.?", "", raw)
        raw = re.sub(r"[^a-z0-9]+", "", raw)
        return raw
