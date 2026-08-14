from __future__ import annotations

from revenue_hunter.filters.taxonomy import normalize_funding, normalize_revenue, size_band_from_employees
from revenue_hunter.models.types import (
    DecisionMakerContact,
    FilterMatch,
    PainPoint,
    PriorityGrade,
    RevenueDossier,
    RevenueHunterInput,
    ScoreComponent,
    ServiceMatchResult,
    WebsiteIntelligence,
    WhyNowV2,
)


CASE_STUDIES: dict[str, list[str]] = {
    "COMAI": ["Ecommerce support deflection 40%", "WhatsApp commerce conversion lift"],
    "Custom AI": ["Ops forecasting model for mid-market SaaS", "Document AI for legal intake"],
    "Website": ["B2B site rebuild + SEO lift", "Real estate lead-gen redesign"],
    "Mobile App": ["Fintech onboarding app", "Healthcare patient app MVP"],
    "SaaS": ["Multi-tenant B2B platform build", "Subscription billing + admin"],
    "Internal Software": ["Logistics ops console", "Manufacturing work-order system"],
    "Automation": ["Hire-to-onboard workflow automation", "Invoice reconciliation bots"],
    "AI Chatbot": ["Support chatbot deflecting L1 tickets", "Lead-qual chatbot on marketing site"],
    "CRM": ["HubSpot → custom sales OS", "Pipeline hygiene automation"],
    "ERP": ["Inventory + finance consolidation", "NetSuite integration layer"],
    "Multi Agent Systems": ["Multi-agent research ops", "Agent orchestration for support + CRM"],
}

OBJECTIONS: dict[str, list[str]] = {
    "default": [
        "We already have an internal team",
        "Budget is locked this quarter",
        "We tried an agency before",
        "Need security / compliance review",
    ],
}


class DossierBuilder:
    """Compose the full revenue dossier — everything founders need in one place."""

    def build(
        self,
        item: RevenueHunterInput,
        *,
        filter_match: FilterMatch,
        service: ServiceMatchResult,
        pains: list[PainPoint],
        website: WebsiteIntelligence,
        why_now: WhyNowV2,
        priority_grade: PriorityGrade,
        revenue_score: float,
        proceed_to_campaign: bool,
        score_breakdown: list[ScoreComponent],
    ) -> RevenueDossier:
        decision_makers = self._decision_makers(item)
        emails = self._emails(item, decision_makers)
        phones = self._phones(item, decision_makers)
        size = item.company_size_band or size_band_from_employees(item.employee_count)
        funding = normalize_funding(item.funding_stage) or item.funding_stage
        revenue = normalize_revenue(item.revenue_band) or item.revenue_band

        summary = (
            f"{item.company_name} — {item.industry or 'company'} "
            f"({filter_match.matched_country or item.country or 'n/a'}), "
            f"{size or 'size unknown'}, grade {priority_grade.value}."
        )
        business = (
            f"{item.business_model or 'B2B/B2C'} business in {item.industry or 'unknown'} "
            f"with signals: {', '.join(item.signals[:5]) or 'n/a'}."
        )
        proposal = (
            f"Lead with {service.service} scoped to {pains[0].problem if pains else 'priority ops gap'}. "
            f"Open with evidence: {'; '.join(why_now.evidence_chain[:3]) or 'ICP fit'}. "
            f"Anchor budget at {why_now.expected_budget}."
        )
        meeting = (
            "Book a 25-minute discovery: (1) confirm pain owner, "
            "(2) quantify cost of status quo, (3) show 1 relevant case study, "
            "(4) propose next-step workshop."
        )
        portfolio = f"Lead portfolio: {service.service} — pair with adjacent Automation or AI Chatbot if support-heavy."

        return RevenueDossier(
            company_id=item.company_id,
            company_name=item.company_name,
            company_summary=summary,
            business=business,
            products=list(item.products),
            technology=list(item.technologies),
            employees=item.employee_count,
            revenue=revenue,
            funding=funding,
            hiring=list(item.hiring_roles),
            decision_makers=decision_makers,
            emails=emails,
            phones=phones,
            social=list(item.social_profiles),
            pain_points=pains,
            buying_signals=list(dict.fromkeys(item.signals + item.growth_signals))[:20],
            recommended_service=service.service,
            service_confidence=service.confidence,
            expected_budget=why_now.expected_budget,
            expected_timeline=why_now.expected_timeline,
            probability=why_now.probability,
            proposal_strategy=proposal,
            meeting_strategy=meeting,
            objections=list(OBJECTIONS["default"]),
            portfolio_recommendation=portfolio,
            case_studies=list(CASE_STUDIES.get(service.service, CASE_STUDIES["Custom AI"])),
            website=website,
            why_now=why_now,
            priority_grade=priority_grade,
            revenue_score=revenue_score,
            proceed_to_campaign=proceed_to_campaign,
            score_breakdown=score_breakdown,
            evidence_chain=why_now.evidence_chain,
        )

    def _decision_makers(self, item: RevenueHunterInput) -> list[DecisionMakerContact]:
        out: list[DecisionMakerContact] = []
        for dm in item.decision_makers:
            out.append(
                DecisionMakerContact(
                    name=str(dm.get("name") or dm.get("full_name") or "Unknown"),
                    role=str(dm.get("role") or dm.get("title") or "") or None,
                    email=str(dm["email"]) if dm.get("email") else None,
                    phone=str(dm["phone"]) if dm.get("phone") else None,
                    linkedin=str(dm.get("linkedin") or dm.get("linkedin_url") or "") or None,
                    confidence=float(dm.get("confidence") or 0.0),
                )
            )
        return out

    def _emails(self, item: RevenueHunterInput, dms: list[DecisionMakerContact]) -> list[str]:
        emails = [e for e in (dm.email for dm in dms) if e]
        for c in item.contacts:
            if c.get("email"):
                emails.append(str(c["email"]))
            if c.get("type") == "email" and c.get("value"):
                emails.append(str(c["value"]))
        return list(dict.fromkeys(emails))

    def _phones(self, item: RevenueHunterInput, dms: list[DecisionMakerContact]) -> list[str]:
        phones = [p for p in (dm.phone for dm in dms) if p]
        for c in item.contacts:
            if c.get("phone"):
                phones.append(str(c["phone"]))
            if c.get("type") == "phone" and c.get("value"):
                phones.append(str(c["value"]))
        return list(dict.fromkeys(phones))
