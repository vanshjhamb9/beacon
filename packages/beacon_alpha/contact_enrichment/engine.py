from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import AttributedValue, ContactEnrichmentResult, UNKNOWN
from revenue_quality_recovery.contact_waterfall.engine import ContactWaterfallEngine
from revenue_quality_recovery.website_crawler.engine import WebsiteCrawlerEngine

ALPHA_WATERFALL = (
    "website",
    "contact_page",
    "about_page",
    "footer",
    "careers",
    "json_ld",
    "mailto",
    "schema_org",
    "linkedin_company",
    "public_decision_makers",
    "public_email_providers",
    "verification",
)


class ContactEnrichmentEngine:
    """Rule 3 — first-class contact enrichment waterfall. Never fabricate."""

    def __init__(self) -> None:
        self.crawler = WebsiteCrawlerEngine()
        self.waterfall = ContactWaterfallEngine()

    def enrich(self, payload: dict[str, Any]) -> ContactEnrichmentResult:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        crawl = self.crawler.crawl(payload)
        wf = self.waterfall.enrich(payload, crawl=crawl)

        emails = [self._to_attr(e) for e in wf.emails]
        phones = [self._to_attr(p) for p in wf.phones]
        linkedin: list[AttributedValue] = []
        sources_used: list[str] = []
        evidence: list[str] = []

        # Map crawl pages to alpha waterfall labels
        page_map = {p.page_type: p for p in crawl.pages}
        for label, page_type in (
            ("website", None),
            ("contact_page", "contact"),
            ("about_page", "about"),
            ("footer", "footer"),
            ("careers", "careers"),
        ):
            if label == "website" and (payload.get("website") or crawl.emails or crawl.phones):
                sources_used.append(label)
            elif page_type and page_map.get(page_type) and page_map[page_type].found:
                sources_used.append(label)

        if crawl.schema_org:
            sources_used.append("schema_org")
            sources_used.append("json_ld")
            evidence.append("schema_org_present")
        if any(e.verification == "mailto_link" or "mailto" in (e.evidence or []) for e in crawl.emails):
            sources_used.append("mailto")
        if payload.get("linkedin_company") or payload.get("linkedin_url") or crawl.social.get("linkedin"):
            sources_used.append("linkedin_company")
            li = payload.get("linkedin_company") or payload.get("linkedin_url") or crawl.social["linkedin"].value
            linkedin.append(
                AttributedValue.of(li, source="linkedin_company", collected_at=collected_at, confidence=85.0, evidence=["linkedin_observed"])
            )
        if payload.get("decision_makers") or wf.decision_makers:
            sources_used.append("public_decision_makers")
        if payload.get("licensed_contacts") or payload.get("provider_contacts") or payload.get("public_email_providers"):
            sources_used.append("public_email_providers")
        if payload.get("verified_emails") or payload.get("mx_valid") or payload.get("mx_validated_emails"):
            sources_used.append("verification")

        for s in wf.sources_tried:
            if s.found and s.source not in sources_used:
                # keep rqp names too for audit
                evidence.append(f"rqp_waterfall:{s.source}")

        dms: list[dict[str, Any]] = []
        for person in payload.get("decision_makers") or []:
            if not isinstance(person, dict) or not person.get("name"):
                continue
            dms.append(
                {
                    "name": person.get("name"),
                    "title": person.get("role") or person.get("title") or UNKNOWN,
                    "email": person.get("email") or person.get("work_email") or UNKNOWN,
                    "phone": person.get("phone") or person.get("business_phone") or UNKNOWN,
                    "linkedin": person.get("linkedin") or person.get("linkedin_url") or UNKNOWN,
                    "confidence": float(person.get("confidence") or 70),
                    "source": person.get("source") or "public_decision_makers",
                    "collected_at": person.get("collected_at") or collected_at,
                }
            )
        for dm in wf.decision_makers:
            if isinstance(dm.value, dict) and dm.value.get("name"):
                dms.append(
                    {
                        "name": dm.value.get("name"),
                        "title": dm.value.get("role") or UNKNOWN,
                        "email": dm.value.get("email") or UNKNOWN,
                        "phone": dm.value.get("phone") or UNKNOWN,
                        "linkedin": dm.value.get("linkedin") or UNKNOWN,
                        "confidence": dm.confidence or 60,
                        "source": dm.source,
                        "collected_at": dm.collected_at or collected_at,
                    }
                )

        # Dedupe DMs by name
        seen: set[str] = set()
        unique_dms = []
        for d in dms:
            key = str(d["name"]).lower()
            if key in seen:
                continue
            seen.add(key)
            unique_dms.append(d)

        conf = min(
            100.0,
            round(
                (15.0 * len(set(sources_used)))
                + (10.0 if emails else 0)
                + (8.0 if phones else 0)
                + (10.0 if unique_dms else 0),
                2,
            ),
        )
        evidence.extend([f"emails:{len(emails)}", f"phones:{len(phones)}", f"dms:{len(unique_dms)}"])
        return ContactEnrichmentResult(
            emails=emails[:20],
            phones=phones[:20],
            linkedin=linkedin[:5],
            decision_makers=unique_dms[:20],
            sources_used=list(dict.fromkeys(sources_used)),
            confidence=conf,
            evidence=evidence,
        )

    def _to_attr(self, field: Any) -> AttributedValue:
        if isinstance(field, AttributedValue):
            return field
        # RQP AttributedField or similar
        return AttributedValue.of(
            getattr(field, "value", None),
            source=str(getattr(field, "source", UNKNOWN) or UNKNOWN),
            collected_at=getattr(field, "collected_at", None),
            confidence=getattr(field, "confidence", None),
            evidence=list(getattr(field, "evidence", None) or []),
        )
