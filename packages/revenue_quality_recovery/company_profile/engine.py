from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import (
    AttributedField,
    CompanyProfile,
    ContactConfidenceResult,
    EvidencePanel,
    IdentityValidationResult,
    RevenueVerdict,
    SalesReadyGateResult,
    WebsiteCrawlResult,
    UNKNOWN,
)


class CompanyProfileBuilder:
    """Rule 8 — one coherent company profile for the founder page."""

    def build(
        self,
        payload: dict[str, Any],
        *,
        gate: SalesReadyGateResult,
        identity: IdentityValidationResult,
        crawl: WebsiteCrawlResult,
        contacts: ContactConfidenceResult,
        evidence_panel: EvidencePanel,
    ) -> CompanyProfile:
        company_id = str(payload.get("company_id") or payload.get("id") or UNKNOWN)
        name = str(payload.get("company_name") or payload.get("legal_name") or identity.legal_name.value or UNKNOWN)
        service = (
            payload.get("recommended_service")
            or payload.get("ai_service_match")
            or self._first_service(payload)
            or UNKNOWN
        )
        raw_intent = payload.get("buying_intent") or payload.get("intent_level")
        if not raw_intent and payload.get("signals"):
            sig0 = payload["signals"][0]
            raw_intent = sig0.get("signal") or sig0.get("value") if isinstance(sig0, dict) else sig0
        intent = str(raw_intent) if raw_intent else UNKNOWN
        if isinstance(raw_intent, dict):
            intent = str(raw_intent.get("signal") or raw_intent.get("value") or UNKNOWN)

        pain = str(payload.get("pain") or payload.get("pain_point") or UNKNOWN)
        hiring = []
        for s in payload.get("signals") or []:
            val = str(s.get("value") if isinstance(s, dict) else s)
            if "hir" in val.lower() or "career" in val.lower() or "job" in val.lower():
                hiring.append(val)
        for t in payload.get("timeline") or []:
            if isinstance(t, dict) and "hir" in str(t.get("summary") or t.get("signal_type") or "").lower():
                hiring.append(str(t.get("summary") or t.get("signal_type")))

        techs = [str(t.get("name") if isinstance(t, dict) else t) for t in (payload.get("technologies") or []) if t]
        emails = [c.email for c in contacts.contacts if c.email.value != UNKNOWN]
        phones = [c.phone for c in contacts.contacts if c.phone.value != UNKNOWN]
        for e in crawl.emails:
            if e.value != UNKNOWN and not any(x.value == e.value for x in emails):
                emails.append(e)
        for p in crawl.phones:
            if p.value != UNKNOWN and not any(x.value == p.value for x in phones):
                phones.append(p)

        sales_ready = gate.verdict == RevenueVerdict.SALES_READY and identity.accepted
        outreach = UNKNOWN
        if sales_ready and emails:
            outreach = "Email outreach using verified business address"
        elif sales_ready and phones:
            outreach = "Phone outreach using verified public number"
        elif sales_ready and any(c.linkedin.value != UNKNOWN for c in contacts.contacts):
            outreach = "LinkedIn outreach to verified decision maker"
        elif sales_ready:
            outreach = "Use contact form / LinkedIn company page"
        else:
            outreach = "Do not contact — rejected or incomplete"

        confidence = round((gate.confidence + identity.confidence + contacts.average_confidence) / 3.0, 2)

        return CompanyProfile(
            company_id=company_id,
            company_name=name,
            logo=payload.get("logo") or payload.get("logo_url") or (crawl.open_graph or {}).get("image") or UNKNOWN,
            website=payload.get("website") or payload.get("primary_domain") or UNKNOWN,
            industry=payload.get("industry") or UNKNOWN,
            hq=payload.get("country") or payload.get("hq") or payload.get("location") or UNKNOWN,
            employees=payload.get("employees") or payload.get("employee_estimate") or UNKNOWN,
            funding=payload.get("funding") or UNKNOWN,
            founded=payload.get("founded") or payload.get("founded_year") or UNKNOWN,
            revenue_estimate=payload.get("revenue_estimate") or payload.get("estimated_deal") or UNKNOWN,
            tech_stack=techs[:20],
            hiring=hiring[:10],
            intent=str(intent) if intent else UNKNOWN,
            pain=pain,
            recommended_service=str(service),
            decision_makers=contacts.contacts,
            verified_emails=emails[:20],
            verified_phones=phones[:20],
            linkedin=payload.get("linkedin_company") or payload.get("linkedin_company_url") or payload.get("linkedin_url") or UNKNOWN,
            confidence=confidence,
            evidence_timeline=evidence_panel.items,
            outreach_recommendation=outreach,
            sales_ready_badge=sales_ready,
            verdict=RevenueVerdict.SALES_READY if sales_ready else RevenueVerdict.REJECTED,
            scoring_version="rqp-v1",
            evidence=[
                f"badge:{sales_ready}",
                f"verdict:{RevenueVerdict.SALES_READY.value if sales_ready else RevenueVerdict.REJECTED.value}",
                f"confidence:{confidence}",
            ],
        )

    def _first_service(self, payload: dict[str, Any]) -> Any:
        services = payload.get("recommended_services") or payload.get("services") or []
        if services and isinstance(services[0], dict):
            return services[0].get("recommended_service") or services[0].get("service")
        if services:
            return services[0]
        return None
