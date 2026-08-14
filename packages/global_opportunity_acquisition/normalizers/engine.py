from __future__ import annotations

import hashlib
import re

from global_opportunity_acquisition.models.types import RawSignal


class NormalizerEngine:
    def normalize(self, signals: list[RawSignal]) -> list[dict]:
        out = []
        for s in signals:
            domain = (s.company_domain or "").lower().strip() or self._guess_domain(s.company_name)
            key = self._canonical(s.company_name, domain)
            out.append(
                {
                    "canonical_key": key,
                    "company_name": s.company_name.strip(),
                    "company_domain": domain or None,
                    "connector_id": s.connector_id,
                    "title": s.title,
                    "body": s.body,
                    "url": s.url,
                    "signal_id": s.signal_id,
                }
            )
        return out

    def _canonical(self, name: str, domain: str | None) -> str:
        base = (domain or re.sub(r"[^a-z0-9]+", "", name.lower())).strip()
        return hashlib.sha256(base.encode()).hexdigest()[:16]

    def _guess_domain(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "", name.lower())
        return f"{slug}.example" if slug else ""
