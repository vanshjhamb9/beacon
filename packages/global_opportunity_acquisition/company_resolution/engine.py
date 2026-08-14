from __future__ import annotations

import hashlib
import re


class CompanyResolutionEngine:
    def resolve(self, name: str, domain: str | None = None) -> str:
        slug = (domain or "").lower().strip() or re.sub(r"[^a-z0-9]+", "", name.lower())
        return hashlib.sha256(slug.encode()).hexdigest()[:16]
