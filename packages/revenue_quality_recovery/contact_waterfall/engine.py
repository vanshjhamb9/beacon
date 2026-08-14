from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import (
    AttributedField,
    ContactWaterfallResult,
    WaterfallSourceResult,
    WebsiteCrawlResult,
    UNKNOWN,
)

WATERFALL = (
    "company_website",
    "contact_page",
    "about_page",
    "leadership_page",
    "press_page",
    "linkedin_company",
    "decision_discovery",
    "licensed_providers",
    "google_public_search",
    "verification",
    "mx_validation",
)

SOURCE_BOOST = {
    "company_website": 8.0,
    "contact_page": 12.0,
    "about_page": 6.0,
    "leadership_page": 14.0,
    "press_page": 5.0,
    "linkedin_company": 10.0,
    "decision_discovery": 15.0,
    "licensed_providers": 12.0,
    "google_public_search": 4.0,
    "verification": 10.0,
    "mx_validation": 15.0,
}


class ContactWaterfallEngine:
    """Rule 2 — multi-source contact enrichment waterfall. Never invent."""

    def enrich(
        self,
        payload: dict[str, Any],
        *,
        crawl: WebsiteCrawlResult | None = None,
    ) -> ContactWaterfallResult:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        sources: list[WaterfallSourceResult] = []
        contacts: list[dict[str, Any]] = []
        emails: list[AttributedField] = []
        phones: list[AttributedField] = []
        dms: list[AttributedField] = []
        confidence = 0.0
        evidence: list[str] = []

        buckets = self._buckets(payload, crawl)

        for source in WATERFALL:
            items = buckets.get(source) or []
            found = len(items) > 0
            boost = SOURCE_BOOST[source] if found else 0.0
            if found:
                confidence += boost
                evidence.append(f"waterfall:{source}:{len(items)}")
                for item in items:
                    contacts.append({**item, "waterfall_source": source})
                    self._absorb(item, source, collected_at, emails, phones, dms)
            sources.append(
                WaterfallSourceResult(
                    source=source,
                    found=found,
                    contacts_found=len(items),
                    confidence_boost=boost,
                    evidence=[f"{source}:{'hit' if found else 'miss'}"],
                )
            )

        # Deduplicate emails/phones by value
        emails = self._dedupe_fields(emails)
        phones = self._dedupe_fields(phones)
        dms = self._dedupe_fields(dms)

        return ContactWaterfallResult(
            sources_tried=sources,
            contacts=contacts,
            total_confidence=min(100.0, round(confidence, 2)),
            emails=emails,
            phones=phones,
            decision_makers=dms,
            evidence=evidence or ["waterfall_empty"],
        )

    def _buckets(self, payload: dict[str, Any], crawl: WebsiteCrawlResult | None) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {s: [] for s in WATERFALL}

        if payload.get("website") or (crawl and (crawl.emails or crawl.phones)):
            for e in (crawl.emails if crawl else [])[:5]:
                out["company_website"].append({"email": e.value, "source": "company_website"})
            for p in (crawl.phones if crawl else [])[:5]:
                out["company_website"].append({"phone": p.value, "source": "company_website"})
            for person in (crawl.founders + crawl.executives) if crawl else []:
                val = person.value if isinstance(person.value, dict) else {"name": person.value}
                out["company_website"].append({**val, "source": "company_website"})

        pages = {p.page_type: p for p in (crawl.pages if crawl else [])}
        if pages.get("contact") and pages["contact"].found:
            for e in payload.get("contact_page_emails") or (crawl.emails if crawl else [])[:3]:
                val = e.value if hasattr(e, "value") else e
                out["contact_page"].append({"email": val, "source": "contact_page"})
            for p in payload.get("contact_page_phones") or []:
                out["contact_page"].append({"phone": p, "source": "contact_page"})

        if pages.get("about") and pages["about"].found:
            for person in payload.get("about_people") or []:
                if isinstance(person, dict) and person.get("name"):
                    out["about_page"].append({**person, "source": "about_page"})

        if pages.get("leadership") and pages["leadership"].found:
            for person in payload.get("leadership") or payload.get("decision_makers") or []:
                if isinstance(person, dict) and person.get("name"):
                    out["leadership_page"].append({**person, "source": "leadership_page"})

        for person in payload.get("press_mentions") or []:
            if isinstance(person, dict) and person.get("name"):
                out["press_page"].append({**person, "source": "press_page"})

        if payload.get("linkedin_company") or payload.get("linkedin_company_url") or payload.get("linkedin_url"):
            out["linkedin_company"].append(
                {
                    "linkedin": payload.get("linkedin_company")
                    or payload.get("linkedin_company_url")
                    or payload.get("linkedin_url"),
                    "source": "linkedin_company",
                }
            )
            for person in payload.get("linkedin_people") or []:
                if isinstance(person, dict) and person.get("name"):
                    out["linkedin_company"].append({**person, "source": "linkedin_company"})

        for person in payload.get("decision_makers") or payload.get("decision_discovery") or []:
            if isinstance(person, dict) and person.get("name"):
                # decision_discovery list may be nested
                out["decision_discovery"].append({**person, "source": person.get("source") or "decision_discovery"})

        if isinstance(payload.get("decision_discovery"), dict):
            for person in payload["decision_discovery"].get("people") or []:
                if isinstance(person, dict) and person.get("name"):
                    out["decision_discovery"].append({**person, "source": "decision_discovery"})

        for person in payload.get("licensed_contacts") or payload.get("provider_contacts") or []:
            if isinstance(person, dict) and (person.get("email") or person.get("name")):
                out["licensed_providers"].append({**person, "source": "licensed_providers"})

        for person in payload.get("google_public_results") or payload.get("public_search") or []:
            if isinstance(person, dict) and (person.get("email") or person.get("name")):
                out["google_public_search"].append({**person, "source": "google_public_search"})

        for email in payload.get("verified_emails") or []:
            out["verification"].append({"email": email, "source": "verification", "verification": "verified"})
        for phone in payload.get("verified_phones") or []:
            out["verification"].append({"phone": phone, "source": "verification", "verification": "verified"})

        for email in payload.get("mx_validated_emails") or []:
            out["mx_validation"].append({"email": email, "source": "mx_validation", "verification": "mx_valid"})
        if payload.get("mx_valid") and payload.get("emails"):
            for email in payload.get("emails") or []:
                out["mx_validation"].append({"email": email, "source": "mx_validation", "verification": "mx_valid"})

        return out

    def _absorb(
        self,
        item: dict[str, Any],
        source: str,
        collected_at: Any,
        emails: list[AttributedField],
        phones: list[AttributedField],
        dms: list[AttributedField],
    ) -> None:
        verification = str(item.get("verification") or "unverified")
        conf = float(item.get("confidence") or SOURCE_BOOST.get(source, 5.0) + 50.0)
        if item.get("email"):
            emails.append(
                AttributedField.of(
                    item["email"],
                    source=source,
                    collected_at=collected_at,
                    confidence=min(98.0, conf),
                    verification=verification,
                    evidence=[f"email_from:{source}"],
                )
            )
        if item.get("phone"):
            phones.append(
                AttributedField.of(
                    item["phone"],
                    source=source,
                    collected_at=collected_at,
                    confidence=min(95.0, conf),
                    verification=verification,
                    evidence=[f"phone_from:{source}"],
                )
            )
        if item.get("name") and item.get("role"):
            dms.append(
                AttributedField.of(
                    {"name": item["name"], "role": item["role"], "email": item.get("email"), "linkedin": item.get("linkedin") or item.get("linkedin_url")},
                    source=source,
                    collected_at=collected_at,
                    confidence=min(95.0, conf),
                    verification=verification,
                    evidence=[f"dm_from:{source}"],
                )
            )

    def _dedupe_fields(self, fields: list[AttributedField]) -> list[AttributedField]:
        seen: set[str] = set()
        out: list[AttributedField] = []
        for f in sorted(fields, key=lambda x: x.confidence or 0, reverse=True):
            key = str(f.value)
            if key in seen or f.value == UNKNOWN:
                continue
            seen.add(key)
            out.append(f)
        return out
