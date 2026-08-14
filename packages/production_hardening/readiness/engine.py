from __future__ import annotations

from typing import Any

from production_hardening.models.types import ContactReadiness, ContactReadinessStatus


class ContactReadinessEngine:
    """Classify contact readiness; founder queue only CONTACT_READY / SALES_READY."""

    def evaluate(self, payload: dict[str, Any]) -> ContactReadiness:
        website = bool(payload.get("website") or payload.get("primary_domain") or payload.get("official_domain"))
        emails = [str(e).strip() for e in (payload.get("emails") or []) if str(e).strip()]
        if payload.get("verified_email"):
            emails.append(str(payload["verified_email"]))
        emails = list(dict.fromkeys(emails))
        phones = [str(p).strip() for p in (payload.get("phones") or []) if str(p).strip()]
        if payload.get("verified_phone"):
            phones.append(str(payload["verified_phone"]))
        phones = list(dict.fromkeys(phones))
        dms = list(payload.get("decision_makers") or [])
        has_dm = bool(dms) or bool(payload.get("has_decision_maker"))
        has_linkedin = bool(payload.get("linkedin_url") or payload.get("linkedin_company_url") or payload.get("has_linkedin"))
        has_form = bool(payload.get("contact_form") or payload.get("has_contact_form"))
        has_evidence = bool(payload.get("business_evidence") or payload.get("has_business_evidence") or payload.get("evidence"))
        has_email = bool(emails)
        has_phone = bool(phones)

        evidence: list[str] = []
        if website:
            evidence.append("website")
        if has_email:
            evidence.append(f"emails:{len(emails)}")
        if has_form:
            evidence.append("contact_form")
        if has_phone:
            evidence.append(f"phones:{len(phones)}")
        if has_dm:
            evidence.append(f"decision_makers:{len(dms) or 1}")
        if has_linkedin:
            evidence.append("linkedin")
        if has_evidence:
            evidence.append("business_evidence")

        status = ContactReadinessStatus.NOT_READY
        why = None
        engine = None
        if has_email and has_phone and has_dm and has_linkedin and website and has_evidence:
            status = ContactReadinessStatus.SALES_READY
        elif has_email or has_form:
            status = ContactReadinessStatus.CONTACT_READY
        elif website:
            status = ContactReadinessStatus.PARTIAL
            why = "Website present but no verified email or contact form"
            engine = "lead_enrichment"
        else:
            why = "No website and no verified contact channels"
            engine = "lead_enrichment"

        return ContactReadiness(
            status=status,
            has_website=website,
            has_verified_email=has_email,
            has_contact_form=has_form,
            has_phone=has_phone,
            has_decision_maker=has_dm,
            has_linkedin=has_linkedin,
            has_business_evidence=has_evidence,
            emails=emails,
            phones=phones,
            decision_makers=dms if isinstance(dms, list) else [],
            evidence=evidence,
            why_unavailable=why,
            responsible_engine=engine,
        )

    def visible_in_founder_queue(self, readiness: ContactReadiness) -> bool:
        return readiness.status in {
            ContactReadinessStatus.CONTACT_READY,
            ContactReadinessStatus.SALES_READY,
        }
