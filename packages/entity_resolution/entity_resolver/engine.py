"""Entity resolver — normalize aliases into one candidate. Never invent websites."""

from __future__ import annotations

import re
from typing import Any

from entity_resolution.models.types import EntityCandidate, OfficialWebsite, UNKNOWN
from intelligence.entity_resolution.normalization import normalize_company_name
from production_hardening.admission.engine import FAKE_NAME_PATTERNS

STOP = frozenset({"link", "discussion", "the", "a", "an", "your", "our", "new", "ai", "app"})


class EntityResolverEngine:
    def resolve(self, payload: dict[str, Any], *, website: OfficialWebsite | None = None) -> EntityCandidate:
        names: list[str] = []
        for key in ("company_name", "legal_name", "organization", "product_name", "name"):
            if payload.get(key):
                names.append(str(payload[key]).strip())
        meta = payload.get("metadata") or {}
        for h in meta.get("company_hints") or payload.get("mentions") or []:
            names.append(str(h).strip())
        title = str(payload.get("title") or "")
        source = str(payload.get("source") or "").lower()
        if source == "product_hunt" and title:
            part = re.split(r"\s+[—\-–|:]\s+", title, maxsplit=1)[0].strip()
            # strip version suffixes like "2.0"
            part = re.sub(r"\s+\d+(\.\d+)*$", "", part).strip()
            if part:
                names.append(part)
        m = re.search(r"\bShow HN:\s*([A-Za-z0-9][A-Za-z0-9.&+\- ]{1,60})", title, re.I)
        if m:
            names.append(m.group(1).strip())

        cleaned: list[str] = []
        seen: set[str] = set()
        for n in names:
            if not self._valid(n):
                continue
            key = normalize_company_name(n)
            if not key or key in seen:
                continue
            seen.add(key)
            cleaned.append(n)

        primary = cleaned[0] if cleaned else UNKNOWN
        aliases = cleaned[1:8]
        # Domain-derived alias if consistent
        if website and website.domain and primary != UNKNOWN:
            label = website.domain.split(".")[0].replace("-", " ")
            if normalize_company_name(label) and normalize_company_name(label) not in seen:
                aliases.append(label.title())

        normalized = normalize_company_name(primary) if primary != UNKNOWN else UNKNOWN
        org = primary if primary != UNKNOWN else None
        return EntityCandidate(
            name=primary,
            aliases=aliases,
            organization=org,
            official_website=website.website if website and website.discovered else None,
            domain=website.domain if website and website.discovered else None,
            normalized_key=normalized,
            evidence=[f"name:{primary}", f"aliases:{len(aliases)}", f"key:{normalized}"],
        )

    def _valid(self, name: str) -> bool:
        n = (name or "").strip()
        if len(n) < 2 or len(n) > 80:
            return False
        low = n.lower()
        if low in FAKE_NAME_PATTERNS or low in STOP:
            return False
        if normalize_company_name(n) in {"", "unknown", "none", "link"}:
            return False
        return True
