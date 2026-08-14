from __future__ import annotations

from typing import Any

from beacon_alpha.contact_enrichment.engine import ContactEnrichmentEngine
from ground_truth.models.types import AttributedField, ContactWaterfallV2Result, UNKNOWN
from revenue_quality_recovery.website_crawler.engine import WebsiteCrawlerEngine

WATERFALL_V2 = (
    "website",
    "contact_page",
    "about",
    "team",
    "privacy",
    "terms",
    "footer",
    "json_ld",
    "mailto",
    "schema_org",
    "linkedin_company",
    "decision_makers",
    "public_emails",
    "mx_validation",
    "hunter_api",
    "apollo",
    "clearbit",
    "people_data_labs",
)


class ContactWaterfallV2Engine:
    """Rule 3 — Contact Waterfall 2.0. Optional providers only when payload supplies results. Never fabricate."""

    def __init__(self) -> None:
        self.base = ContactEnrichmentEngine()
        self.crawler = WebsiteCrawlerEngine()

    def enrich(self, payload: dict[str, Any]) -> ContactWaterfallV2Result:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        base = self.base.enrich(payload)
        crawl = self.crawler.crawl(payload)

        tried = list(WATERFALL_V2)
        hit: list[str] = []
        evidence: list[str] = list(base.evidence)

        page_map = {p.page_type: p for p in crawl.pages}
        mapping = {
            "website": bool(payload.get("website") or base.emails or base.phones),
            "contact_page": bool(page_map.get("contact") and page_map["contact"].found),
            "about": bool(page_map.get("about") and page_map["about"].found),
            "team": bool(page_map.get("team") and page_map["team"].found) or bool(payload.get("team")),
            "privacy": bool(page_map.get("privacy") and page_map["privacy"].found) or bool(payload.get("privacy_page")),
            "terms": bool(payload.get("terms_page") or payload.get("discovered_pages", {}).get("terms")),
            "footer": bool(page_map.get("footer") and page_map["footer"].found),
            "json_ld": bool(crawl.schema_org),
            "mailto": any("mailto" in (e.evidence or []) or getattr(e, "verification", "") == "mailto_link" for e in crawl.emails),
            "schema_org": bool(crawl.schema_org or payload.get("organization_schema")),
            "linkedin_company": bool(payload.get("linkedin_company") or payload.get("linkedin_url") or base.linkedin),
            "decision_makers": bool(base.decision_makers or payload.get("decision_makers")),
            "public_emails": bool(base.emails or payload.get("emails")),
            "mx_validation": bool(payload.get("mx_valid") or payload.get("mx_validated_emails")),
            "hunter_api": bool(payload.get("hunter_contacts") or payload.get("hunter_api")),
            "apollo": bool(payload.get("apollo_contacts") or payload.get("apollo")),
            "clearbit": bool(payload.get("clearbit_contacts") or payload.get("clearbit")),
            "people_data_labs": bool(payload.get("pdl_contacts") or payload.get("people_data_labs")),
        }
        for src, ok in mapping.items():
            if ok:
                hit.append(src)

        emails = [self._to_attr(e) for e in base.emails]
        phones = [self._to_attr(p) for p in base.phones]
        linkedin = [self._to_attr(l) for l in base.linkedin]

        # Optional provider contacts — only if present (never invent)
        for key, source_name in (
            ("hunter_contacts", "hunter_api"),
            ("apollo_contacts", "apollo"),
            ("clearbit_contacts", "clearbit"),
            ("pdl_contacts", "people_data_labs"),
        ):
            for person in payload.get(key) or []:
                if not isinstance(person, dict):
                    continue
                if person.get("email"):
                    emails.append(
                        AttributedField.of(
                            person["email"],
                            source=source_name,
                            collected_at=collected_at,
                            confidence=float(person.get("confidence") or 70),
                            evidence=[f"provider:{source_name}"],
                        )
                    )
                if person.get("phone"):
                    phones.append(
                        AttributedField.of(
                            person["phone"],
                            source=source_name,
                            collected_at=collected_at,
                            confidence=float(person.get("confidence") or 65),
                            evidence=[f"provider:{source_name}"],
                        )
                    )

        conf = min(100.0, round(12.0 * len(hit) + (10.0 if emails else 0) + (8.0 if phones else 0), 2))
        evidence.extend([f"waterfall_hits:{len(hit)}", f"tried:{len(tried)}"])
        return ContactWaterfallV2Result(
            sources_tried=tried,
            sources_hit=hit,
            emails=self._dedupe(emails)[:20],
            phones=self._dedupe(phones)[:20],
            linkedin=self._dedupe(linkedin)[:10],
            decision_makers=base.decision_makers[:20],
            confidence=conf,
            evidence=evidence,
        )

    def _to_attr(self, field: Any) -> AttributedField:
        if isinstance(field, AttributedField):
            return field
        return AttributedField.of(
            getattr(field, "value", field),
            source=str(getattr(field, "source", UNKNOWN) or UNKNOWN),
            collected_at=getattr(field, "collected_at", None),
            confidence=getattr(field, "confidence", None),
            evidence=list(getattr(field, "evidence", None) or []),
        )

    def _dedupe(self, fields: list[AttributedField]) -> list[AttributedField]:
        seen: set[str] = set()
        out = []
        for f in fields:
            key = str(f.value)
            if key in seen or f.value == UNKNOWN:
                continue
            seen.add(key)
            out.append(f)
        return out
