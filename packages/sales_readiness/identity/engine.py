from __future__ import annotations

from typing import Any

from sales_readiness.models.types import AttributedField, IdentityCompleteness, UNKNOWN


class IdentityCompletenessEngine:
    """Require name, website, domain, industry, country, source, evidence."""

    REQUIRED = ("company_name", "website", "domain", "industry", "country", "source", "evidence")

    def evaluate(self, payload: dict[str, Any]) -> IdentityCompleteness:
        fields: dict[str, AttributedField] = {}
        missing: list[str] = []
        evidence: list[str] = []

        name = payload.get("company_name") or payload.get("name")
        website = payload.get("website") or payload.get("primary_domain")
        domain = payload.get("domain") or website
        industry = payload.get("industry")
        country = payload.get("country") or payload.get("location")
        source = payload.get("source")
        ev = payload.get("evidence") or []

        mapping = {
            "company_name": (name, payload.get("name_source") or source or "company_record"),
            "website": (website, payload.get("website_source") or source or "company_record"),
            "domain": (domain, payload.get("domain_source") or source or "company_record"),
            "industry": (industry, payload.get("industry_source") or source or UNKNOWN),
            "country": (country, payload.get("country_source") or source or UNKNOWN),
            "source": (source, "pipeline"),
            "evidence": (f"{len(ev)} items" if ev else None, source or UNKNOWN),
        }
        for key, (value, src) in mapping.items():
            if value in (None, "", UNKNOWN) or (key == "evidence" and not ev):
                missing.append(key)
                fields[key] = AttributedField.unknown(reason=f"missing_{key}")
            else:
                conf = float(payload.get(f"{key}_confidence") or (90.0 if key != "industry" else 70.0))
                fields[key] = AttributedField.of(
                    value,
                    source=str(src),
                    collected_at=payload.get("collected_at") or payload.get("last_seen_at"),
                    confidence=conf,
                    evidence=[f"{key}_observed"],
                )
                evidence.append(f"has_{key}")

        complete = len(missing) == 0
        return IdentityCompleteness(
            identity_complete=complete,
            missing_fields=missing,
            fields=fields,
            evidence=evidence + ([f"complete:{complete}"]),
        )
