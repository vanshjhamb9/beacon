from __future__ import annotations

from datetime import datetime
from typing import Any

from production_hardening.models.types import IdentityReport

IDENTITY_CONFIDENCE_THRESHOLD = 55.0


class CompanyIdentityValidator:
    """Score company identity completeness; reject below threshold."""

    REQUIRED = (
        "company_name",
        "official_domain",
    )

    OPTIONAL_WEIGHTS = {
        "industry": 10.0,
        "description": 8.0,
        "country": 8.0,
        "linkedin_company_url": 10.0,
        "employee_estimate": 6.0,
        "technology_stack": 8.0,
        "website_title": 5.0,
        "logo_url": 5.0,
        "first_seen_at": 5.0,
        "last_verified_at": 5.0,
    }

    def evaluate(self, payload: dict[str, Any]) -> IdentityReport:
        name = str(payload.get("company_name") or payload.get("name") or "").strip()
        domain = payload.get("official_domain") or payload.get("primary_domain") or payload.get("website")
        domain = str(domain).strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.") if domain else None
        if domain and "/" in domain:
            domain = domain.split("/", 1)[0]

        missing: list[str] = []
        if not name:
            missing.append("company_name")
        if not domain:
            missing.append("official_domain")

        tech = payload.get("technology_stack") or payload.get("technologies") or []
        if isinstance(tech, str):
            tech = [tech]

        confidence = 0.0
        evidence: list[str] = []
        if name:
            confidence += 25.0
            evidence.append("has_name")
        if domain:
            confidence += 25.0
            evidence.append(f"domain:{domain}")

        fields = {
            "industry": payload.get("industry"),
            "description": payload.get("description") or payload.get("memory_summary"),
            "country": payload.get("country") or payload.get("location"),
            "linkedin_company_url": payload.get("linkedin_company_url") or payload.get("linkedin_url"),
            "employee_estimate": payload.get("employee_estimate") or payload.get("employees"),
            "technology_stack": tech,
            "website_title": payload.get("website_title"),
            "logo_url": payload.get("logo_url"),
            "first_seen_at": payload.get("first_seen_at") or payload.get("created_at"),
            "last_verified_at": payload.get("last_verified_at") or payload.get("last_seen_at"),
        }
        for key, weight in self.OPTIONAL_WEIGHTS.items():
            value = fields[key]
            if value:
                confidence += weight
                evidence.append(f"has_{key}")
            else:
                missing.append(key)

        confidence = min(100.0, round(confidence, 2))
        admitted = confidence >= IDENTITY_CONFIDENCE_THRESHOLD and "company_name" not in missing and "official_domain" not in missing

        return IdentityReport(
            company_name=name or "unknown",
            official_domain=domain,
            website_title=fields["website_title"],
            logo_url=fields["logo_url"],
            industry=fields["industry"],
            country=fields["country"],
            linkedin_company_url=fields["linkedin_company_url"],
            description=fields["description"],
            employee_estimate=str(fields["employee_estimate"]) if fields["employee_estimate"] else None,
            technology_stack=[str(t) for t in tech][:20],
            first_seen_at=self._dt(fields["first_seen_at"]),
            last_verified_at=self._dt(fields["last_verified_at"]),
            confidence=confidence,
            admitted=admitted,
            missing_fields=missing,
            evidence=evidence,
        )

    def _dt(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            return None
