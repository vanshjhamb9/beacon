from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from revenue_data_recovery.models.types import AttributedValue, IdentityRecoveryResult, UNKNOWN

IDENTITY_FIELDS = (
    "legal_name",
    "website",
    "domain",
    "country",
    "industry",
    "business_category",
    "description",
    "linkedin_company_url",
    "employee_estimate",
)

PIPELINE_SOURCES = (
    "source_metadata",
    "existing_website",
    "opportunity_evidence",
    "technology_profile",
    "goap_evidence",
    "rss_metadata",
    "public_company_pages",
    "decision_discovery",
    "website_intelligence",
)


class IdentityRecoveryEngine:
    """Recover missing identity from existing evidence — never fabricate."""

    def recover(self, payload: dict[str, Any]) -> IdentityRecoveryResult:
        sources_tried: list[str] = []
        evidence: list[str] = []
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")

        legal_name = self._pick(
            [
                ("source_metadata", payload.get("legal_name") or payload.get("company_name") or payload.get("name")),
                ("opportunity_evidence", self._from_evidence(payload, "company_name", "legal_name")),
                ("goap_evidence", self._nested(payload, "goap", "company_name")),
                ("rss_metadata", self._nested(payload, "rss", "title")),
                ("public_company_pages", self._nested(payload, "public_page", "name")),
                ("decision_discovery", self._nested(payload, "decision_discovery", "company_name")),
            ],
            sources_tried,
            evidence,
            field="legal_name",
            collected_at=collected_at,
            confidence=90.0,
        )

        website = self._pick(
            [
                ("existing_website", payload.get("website") or payload.get("primary_domain")),
                ("source_metadata", payload.get("website_url") or payload.get("homepage")),
                ("opportunity_evidence", self._from_evidence(payload, "website", "url")),
                ("rss_metadata", self._nested(payload, "rss", "link")),
                ("goap_evidence", self._nested(payload, "goap", "website")),
                ("public_company_pages", self._nested(payload, "public_page", "website")),
                ("website_intelligence", self._nested(payload, "website_intelligence", "homepage")),
            ],
            sources_tried,
            evidence,
            field="website",
            collected_at=collected_at,
            confidence=88.0,
        )

        domain_raw = (
            payload.get("domain")
            or payload.get("canonical_domain")
            or self._domain_from_url(website.value if website.value != UNKNOWN else None)
            or self._domain_from_url(payload.get("website"))
            or self._from_evidence(payload, "domain")
        )
        domain = AttributedValue.of(
            self._normalize_domain(domain_raw),
            source="canonical_domain" if domain_raw else UNKNOWN,
            collected_at=collected_at,
            confidence=92.0 if domain_raw else None,
            evidence=["domain_normalized"] if domain_raw else ["missing_domain"],
        )
        if domain.value != UNKNOWN:
            sources_tried.append("canonical_domain")
            evidence.append("has_domain")

        country = self._pick(
            [
                ("source_metadata", payload.get("country") or payload.get("location")),
                ("opportunity_evidence", self._from_evidence(payload, "country", "location")),
                ("public_company_pages", self._nested(payload, "public_page", "country")),
                ("website_intelligence", self._nested(payload, "website_intelligence", "country")),
            ],
            sources_tried,
            evidence,
            field="country",
            collected_at=collected_at,
            confidence=75.0,
        )

        industry = self._pick(
            [
                ("source_metadata", payload.get("industry")),
                ("technology_profile", self._nested(payload, "technology_profile", "industry")),
                ("opportunity_evidence", self._from_evidence(payload, "industry")),
                ("public_company_pages", self._nested(payload, "public_page", "industry")),
            ],
            sources_tried,
            evidence,
            field="industry",
            collected_at=collected_at,
            confidence=70.0,
        )

        business_category = self._pick(
            [
                ("source_metadata", payload.get("business_category") or payload.get("category")),
                ("technology_profile", self._nested(payload, "technology_profile", "category")),
                ("opportunity_evidence", self._from_evidence(payload, "business_category", "category")),
            ],
            sources_tried,
            evidence,
            field="business_category",
            collected_at=collected_at,
            confidence=68.0,
        )

        description = self._pick(
            [
                ("source_metadata", payload.get("description") or payload.get("narrative") or payload.get("memory_summary")),
                ("opportunity_evidence", self._from_evidence(payload, "description", "summary", "narrative")),
                ("rss_metadata", self._nested(payload, "rss", "description")),
                ("public_company_pages", self._nested(payload, "public_page", "description")),
                ("website_intelligence", self._nested(payload, "website_intelligence", "description")),
            ],
            sources_tried,
            evidence,
            field="description",
            collected_at=collected_at,
            confidence=65.0,
        )

        linkedin = self._pick(
            [
                ("source_metadata", payload.get("linkedin_company_url") or payload.get("linkedin_url")),
                ("decision_discovery", self._nested(payload, "decision_discovery", "company_linkedin")),
                ("public_company_pages", self._nested(payload, "public_page", "linkedin")),
                ("opportunity_evidence", self._from_evidence(payload, "linkedin", "linkedin_url")),
            ],
            sources_tried,
            evidence,
            field="linkedin_company_url",
            collected_at=collected_at,
            confidence=80.0,
        )

        employees = self._pick(
            [
                ("source_metadata", payload.get("employees") or payload.get("employee_estimate")),
                ("public_company_pages", self._nested(payload, "public_page", "employees")),
                ("opportunity_evidence", self._from_evidence(payload, "employees", "employee_estimate")),
            ],
            sources_tried,
            evidence,
            field="employee_estimate",
            collected_at=collected_at,
            confidence=60.0,
        )

        fields = {
            "legal_name": legal_name,
            "website": website,
            "domain": domain,
            "country": country,
            "industry": industry,
            "business_category": business_category,
            "description": description,
            "linkedin_company_url": linkedin,
            "employee_estimate": employees,
        }
        missing = [k for k, v in fields.items() if v.value == UNKNOWN]
        # Required for identity complete (employee_estimate optional)
        required = ("legal_name", "website", "domain", "country", "industry", "description")
        required_missing = [k for k in required if fields[k].value == UNKNOWN]
        complete = len(required_missing) == 0
        present = len(IDENTITY_FIELDS) - len(missing)
        confidence = round(100.0 * present / len(IDENTITY_FIELDS), 2)

        for src in PIPELINE_SOURCES:
            if src not in sources_tried and self._source_available(payload, src):
                sources_tried.append(src)

        return IdentityRecoveryResult(
            legal_name=legal_name,
            website=website,
            domain=domain,
            country=country,
            industry=industry,
            business_category=business_category,
            description=description,
            linkedin_company_url=linkedin,
            employee_estimate=employees,
            identity_complete=complete,
            confidence=confidence,
            missing_fields=missing,
            sources_tried=list(dict.fromkeys(sources_tried)),
            evidence=evidence + [f"complete:{complete}", f"confidence:{confidence}"],
        )

    def _pick(
        self,
        candidates: list[tuple[str, Any]],
        sources_tried: list[str],
        evidence: list[str],
        *,
        field: str,
        collected_at: Any,
        confidence: float,
    ) -> AttributedValue:
        for source, value in candidates:
            sources_tried.append(source)
            if value in (None, "", UNKNOWN):
                continue
            evidence.append(f"{field}_from:{source}")
            return AttributedValue.of(
                value,
                source=source,
                collected_at=collected_at,
                confidence=confidence,
                evidence=[f"{field}_observed:{source}"],
            )
        return AttributedValue.unknown(reason=f"missing_{field}")

    def _from_evidence(self, payload: dict[str, Any], *keys: str) -> Any:
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                for key in keys:
                    if item.get(key):
                        return item.get(key)
                summary = item.get("summary") or item.get("text")
                if summary and keys[0] == "description":
                    return summary
            elif isinstance(item, str) and keys[0] in {"description", "narrative"}:
                return item
        return None

    def _nested(self, payload: dict[str, Any], root: str, key: str) -> Any:
        block = payload.get(root)
        if isinstance(block, dict):
            return block.get(key)
        return None

    def _source_available(self, payload: dict[str, Any], source: str) -> bool:
        mapping = {
            "source_metadata": bool(payload.get("source") or payload.get("legal_name") or payload.get("company_name")),
            "existing_website": bool(payload.get("website") or payload.get("primary_domain")),
            "opportunity_evidence": bool(payload.get("evidence")),
            "technology_profile": bool(payload.get("technology_profile") or payload.get("technologies")),
            "goap_evidence": bool(payload.get("goap")),
            "rss_metadata": bool(payload.get("rss")),
            "public_company_pages": bool(payload.get("public_page")),
            "decision_discovery": bool(payload.get("decision_discovery") or payload.get("decision_makers")),
            "website_intelligence": bool(payload.get("website_intelligence")),
        }
        return mapping.get(source, False)

    def _domain_from_url(self, value: Any) -> str | None:
        if not value:
            return None
        return self._normalize_domain(value)

    def _normalize_domain(self, value: Any) -> str | None:
        if not value:
            return None
        raw = str(value).strip().lower()
        if "://" not in raw:
            raw = f"https://{raw}"
        try:
            host = urlparse(raw).hostname or ""
        except Exception:  # noqa: BLE001
            host = str(value).strip().lower()
        host = host.removeprefix("www.")
        return host or None
