from __future__ import annotations

from production_validation.models.types import PlaybookPack


PLAYBOOKS: list[dict[str, object]] = [
    {
        "name": "AI Automation",
        "pain_points": ["manual workflows", "ops bottlenecks", "slow handoffs"],
        "business_triggers": ["hiring ops", "funding", "scaling"],
        "roi": "3–6x in 12 months via hours saved",
        "pricing": "$20k–$45k",
        "case_studies": ["Ops automation for growth-stage SaaS"],
    },
    {
        "name": "Custom AI",
        "pain_points": ["no AI roadmap", "support overload", "knowledge silos"],
        "business_triggers": ["AI initiative", "customer growth"],
        "roi": "Deflect 20–40% repetitive work",
        "pricing": "$45k–$90k",
        "case_studies": ["Custom AI feature for B2B SaaS"],
    },
    {
        "name": "SaaS",
        "pain_points": ["scaling issues", "multi-tenant gaps", "poor onboarding"],
        "business_triggers": ["product-market fit", "series a"],
        "roi": "Faster feature velocity + retention",
        "pricing": "$45k–$90k",
        "case_studies": ["Multi-tenant SaaS MVP"],
    },
    {
        "name": "Web Apps",
        "pain_points": ["poor conversion", "outdated website", "broken journeys"],
        "business_triggers": ["rebrand", "paid acquisition waste"],
        "roi": "Conversion lift 15–40%",
        "pricing": "$12k–$30k",
        "case_studies": ["Conversion rebuild for DTC"],
    },
    {
        "name": "Mobile Apps",
        "pain_points": ["low engagement", "no mobile channel"],
        "business_triggers": ["retention goals", "new market"],
        "roi": "Engagement and retention uplift",
        "pricing": "$30k–$70k",
        "case_studies": ["Consumer mobile MVP"],
    },
    {
        "name": "CRM",
        "pain_points": ["messy pipeline", "no single source of truth"],
        "business_triggers": ["sales team growth"],
        "roi": "Shorter cycle + cleaner forecasting",
        "pricing": "$15k–$40k",
        "case_studies": ["CRM redesign for SMB sales"],
    },
    {
        "name": "Workflow Automation",
        "pain_points": ["manual approvals", "copy-paste ops"],
        "business_triggers": ["headcount freeze", "error rate"],
        "roi": "Cut cycle time 30–60%",
        "pricing": "$18k–$40k",
        "case_studies": ["Approval workflow automation"],
    },
    {
        "name": "MVP Development",
        "pain_points": ["speed to market", "validation risk"],
        "business_triggers": ["seed funding", "prototype deadline"],
        "roi": "Validate market in 6–10 weeks",
        "pricing": "$15k–$35k",
        "case_studies": ["Seed-stage MVP in 8 weeks"],
    },
]


class PlaybookEngine:
    """Reusable playbooks composed for Sales Intelligence / LRE usage."""

    def all(self) -> list[PlaybookPack]:
        return [self._pack(p) for p in PLAYBOOKS]

    def for_service(self, service: str | None) -> PlaybookPack | None:
        if not service:
            return None
        needle = service.lower()
        for p in PLAYBOOKS:
            if needle in str(p["name"]).lower() or str(p["name"]).lower() in needle:
                return self._pack(p)
        return self._pack(PLAYBOOKS[0])

    def _pack(self, raw: dict[str, object]) -> PlaybookPack:
        name = str(raw["name"])
        return PlaybookPack(
            name=name,
            pain_points=list(raw["pain_points"]),  # type: ignore[arg-type]
            business_triggers=list(raw["business_triggers"]),  # type: ignore[arg-type]
            roi=str(raw["roi"]),
            discovery_questions=[
                f"Where does {name.lower()} create the most delay today?",
                "What does success look like in 90 days?",
                "Who owns budget and vendor approval?",
                "What have you already tried?",
            ],
            objections=["Budget", "Timeline", "Internal team", "ROI", "Trust"],
            pricing_guidance=str(raw["pricing"]),
            proposal_structure=[
                "Executive summary",
                "Current-state diagnosis",
                f"Recommended {name} approach",
                "Scope & deliverables",
                "Timeline",
                "Commercials & ROI",
                "Next steps",
            ],
            case_studies=list(raw["case_studies"]),  # type: ignore[arg-type]
            evidence=[f"playbook:{name}", "source:production_validation"],
        )
